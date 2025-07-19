import threading
from typing import Dict, Any

from flask import Blueprint
from flask_socketio import SocketIO, emit
from marshmallow import Schema, fields, ValidationError

from adapters.loggers.logger_adapter import app_logger
from usecases.stt_endless_streaming_use_case import STTEndlessStreamingUseCase


class STTEndlessStreamingConfigSchema(Schema):
    encoding = fields.String(missing="LINEAR16")
    sampleRateHertz = fields.Integer(missing=16000)
    languageCode = fields.String(missing="en-US")
    interimResults = fields.Boolean(missing=True)
    enableWordTimeOffsets = fields.Boolean(missing=False)
    maxAlternatives = fields.Integer(missing=1)
    enableAutomaticPunctuation = fields.Boolean(missing=True)
    model = fields.String(missing="latest_long")


class STTEndlessStreamingController:
    """
    STT Endless Streaming Controller implementation.

    Handles WebSocket connections for continuous speech-to-text streaming
    with automatic restarts to overcome the 4-minute Google Cloud limitation.
    """
    
    def __init__(
        self, socketio: SocketIO, use_case: STTEndlessStreamingUseCase
    ) -> None:
        self.socketio = socketio
        self.use_case = use_case
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.schema = STTEndlessStreamingConfigSchema()
        self.logger = app_logger
        self._register_handlers()

    def _register_handlers(self) -> None:

        @self.socketio.on("connect", namespace="/api/stt/endless")
        def handle_connect(auth=None):
            client_id = self._get_client_id()
            self.logger.info("Endless STT streaming client connected: %s", client_id)

            self.active_sessions[client_id] = {"configured": False, "streaming": False}

            emit(
                "connected",
                {
                    "status": "connected",
                    "message": "Ready for endless streaming",
                    "type": "endless_streaming",
                },
            )

        @self.socketio.on("disconnect", namespace="/api/stt/endless")
        def handle_disconnect():
            try:
                client_id = self._get_client_id()

                if client_id in self.active_sessions:
                    self.use_case.stop_streaming()
                    del self.active_sessions[client_id]
                    self.logger.info(
                        f"Endless streaming client {client_id} disconnected and session cleaned up"
                    )
                else:
                    self.logger.info(
                        f"Endless streaming client {client_id} disconnected (no active session)"
                    )

            except Exception as e:
                self.logger.error(
                    f"Error handling endless streaming disconnect: {str(e)}"
                )
                try:
                    client_id = self._get_client_id()
                    if client_id in self.active_sessions:
                        del self.active_sessions[client_id]
                except Exception:
                    pass

        @self.socketio.on("config", namespace="/api/stt/endless")
        def handle_config(data):
            client_id = self._get_client_id()

            try:

                config_data = self.schema.load(data.get("config", {}))

                self.use_case.execute(config_data)

                if client_id in self.active_sessions:
                    self.active_sessions[client_id]["configured"] = True

                    async def result_callback(result: Dict[str, Any]) -> None:
                        try:
                            event_type = result.get("type", "result")

                            event_mapping = {
                                "streaming_started": "endless_started",
                                "stream_restart": "stream_restart",
                                "final_result": "final_result",
                                "interim_result": "interim_result",
                                "error": "error",
                                "fatal_error": "fatal_error",
                            }

                            client_event = event_mapping.get(event_type, event_type)

                            self.socketio.emit(
                                client_event,
                                result,
                                room=client_id,
                                namespace="/api/stt/endless",
                            )
                        except Exception as e:
                            self.logger.error(
                                f"Error sending endless streaming result to client {client_id}: {str(e)}"
                            )

                    def start_endless_streaming():
                        try:
                            import asyncio

                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(
                                self.use_case.start_streaming(result_callback)
                            )
                        except Exception as e:
                            self.logger.error(
                                f"Error in endless streaming thread: {str(e)}"
                            )
                        finally:
                            loop.close()

                    threading.Thread(
                        target=start_endless_streaming, daemon=True
                    ).start()

                    self.active_sessions[client_id]["streaming"] = True
                    self.logger.info(
                        f"Endless streaming client {client_id} configured and started"
                    )
                    emit(
                        "configured",
                        {
                            "status": "success",
                            "message": "Endless streaming configured and started",
                            "type": "endless_streaming",
                        },
                    )

            except ValidationError as e:
                self.logger.error(
                    f"Endless streaming configuration validation error: {e.messages}"
                )
                emit(
                    "error",
                    {
                        "status": "error",
                        "message": "Invalid endless streaming configuration",
                        "errors": e.messages,
                    },
                )
            except Exception as e:
                self.logger.error(f"Endless streaming configuration error: {str(e)}")
                emit("error", {"status": "error", "message": str(e)})

        @self.socketio.on("audio", namespace="/api/stt/endless")
        def handle_audio(data):
            client_id = self._get_client_id()

            try:
                if client_id not in self.active_sessions:
                    emit(
                        "error",
                        {
                            "status": "error",
                            "message": "No active endless streaming session found",
                        },
                    )
                    return

                if not self.active_sessions[client_id].get("configured"):
                    emit(
                        "error",
                        {
                            "status": "error",
                            "message": "Endless streaming session not configured",
                        },
                    )
                    return

                audio_data = data.get("data")
                if not audio_data:
                    emit(
                        "error",
                        {"status": "error", "message": "No audio data received"},
                    )
                    return

                try:
                    if isinstance(audio_data, list):
                        audio_bytes = bytes(audio_data)
                    else:
                        audio_bytes = audio_data
                except Exception as e:
                    emit(
                        "error",
                        {
                            "status": "error",
                            "message": f"Invalid audio data format: {str(e)}",
                        },
                    )
                    return

                self.use_case.add_audio_data(audio_bytes)

            except Exception as e:
                self.logger.error(f"Endless streaming audio processing error: {str(e)}")
                emit("error", {"status": "error", "message": str(e)})

        @self.socketio.on("stop", namespace="/api/stt/endless")
        def handle_stop():
            client_id = self._get_client_id()

            if client_id in self.active_sessions:
                self.use_case.stop_streaming()
                self.active_sessions[client_id]["streaming"] = False
                self.logger.info(f"Endless streaming stopped for client {client_id}")
                emit(
                    "stopped",
                    {
                        "status": "success",
                        "message": "Endless streaming stopped",
                        "type": "endless_streaming",
                    },
                )
            else:
                emit(
                    "error",
                    {
                        "status": "error",
                        "message": "No active endless streaming session to stop",
                    },
                )

        @self.socketio.on("status", namespace="/api/stt/endless")
        def handle_status():
            client_id = self._get_client_id()

            if client_id in self.active_sessions:
                session = self.active_sessions[client_id]
                emit(
                    "status",
                    {
                        "configured": session.get("configured", False),
                        "streaming": session.get("streaming", False)
                        and self.use_case.is_active(),
                        "type": "endless_streaming",
                    },
                )
            else:
                emit(
                    "status",
                    {
                        "configured": False,
                        "streaming": False,
                        "type": "endless_streaming",
                    },
                )

    def _get_client_id(self) -> str:
        from flask import request

        return request.sid


def create_stt_endless_streaming_blueprint(
    socketio: SocketIO, use_case: STTEndlessStreamingUseCase
) -> Blueprint:
    blueprint = Blueprint("stt_endless_streaming", __name__)
    controller = STTEndlessStreamingController(socketio, use_case)

    @blueprint.route("/health", methods=["GET"])
    def health_check():
        return {
            "status": "healthy",
            "service": "stt_endless_streaming",
            "message": "STT endless streaming service is running",
        }

    return blueprint
