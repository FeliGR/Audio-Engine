import threading
from typing import Any, Dict

from flask import Blueprint, request
from flask_socketio import SocketIO, emit
from marshmallow import Schema, ValidationError, fields

from adapters.loggers.logger_adapter import app_logger
from core.interfaces.stt_controller_interface import STTControllerInterface
from usecases.stt_streaming_use_case import STTStreamingUseCase


class STTStreamingConfigSchema(Schema):
    encoding = fields.String(missing="WEBM_OPUS")
    sampleRateHertz = fields.Integer(missing=48000)
    languageCode = fields.String(missing="en-US")
    interimResults = fields.Boolean(missing=True)
    singleUtterance = fields.Boolean(missing=False)
    enableWordTimeOffsets = fields.Boolean(missing=False)
    maxAlternatives = fields.Integer(missing=1)
    enableAutomaticPunctuation = fields.Boolean(missing=True)
    model = fields.String(missing="latest_long")


class STTStreamingController(STTControllerInterface):
    def __init__(self, socketio: SocketIO, use_case: STTStreamingUseCase) -> None:
        self.socketio = socketio
        self.use_case = use_case
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.schema = STTStreamingConfigSchema()
        self.logger = app_logger
        self._register_handlers()

    def _register_handlers(self) -> None:

        @self.socketio.on("connect", namespace="/api/stt/stream")
        def handle_connect(auth=None):
            client_id = self._get_client_id()
            self.logger.info("STT streaming client connected: %s", client_id)

            self.active_sessions[client_id] = {"configured": False, "streaming": False}

            emit("connected", {"status": "connected", "message": "Ready for streaming"})

        @self.socketio.on("disconnect", namespace="/api/stt/stream")
        def handle_disconnect():
            try:
                client_id = self._get_client_id()

                if client_id in self.active_sessions:

                    self.use_case.stop_streaming()

                    del self.active_sessions[client_id]
                    self.logger.info(
                        f"Client {client_id} disconnected and session cleaned up"
                    )
                else:
                    self.logger.info(
                        f"Client {client_id} disconnected (no active session)"
                    )

            except Exception as e:
                self.logger.error(f"Error handling disconnect: {str(e)}")

                try:
                    client_id = self._get_client_id()
                    if client_id in self.active_sessions:
                        del self.active_sessions[client_id]
                except Exception:
                    pass

        @self.socketio.on("config", namespace="/api/stt/stream")
        def handle_config(data):
            client_id = self._get_client_id()

            try:

                config_data = self.schema.load(data.get("config", {}))

                self.use_case.execute(config_data)

                if client_id in self.active_sessions:
                    self.active_sessions[client_id]["configured"] = True

                    def result_callback(result: Dict[str, Any]) -> None:
                        try:
                            event_type = result.get("type", "result")

                            self.socketio.emit(
                                event_type,
                                result,
                                room=client_id,
                                namespace="/api/stt/stream",
                            )
                        except Exception as e:
                            self.logger.error(
                                f"Error sending result to client {client_id}: {str(e)}"
                            )

                    threading.Thread(
                        target=self._start_streaming_thread,
                        args=(client_id, result_callback),
                        daemon=True,
                    ).start()

                    self.logger.info(
                        f"Client {client_id} configured and streaming started"
                    )
                    emit(
                        "configured",
                        {"status": "success", "message": "Streaming configured"},
                    )

            except ValidationError as e:
                self.logger.error(f"Configuration validation error: {e.messages}")
                emit(
                    "error",
                    {
                        "status": "error",
                        "message": "Invalid configuration",
                        "errors": e.messages,
                    },
                )
            except Exception as e:
                self.logger.error(f"Configuration error: {str(e)}")
                emit("error", {"status": "error", "message": str(e)})

        @self.socketio.on("audio", namespace="/api/stt/stream")
        def handle_audio(data):
            client_id = self._get_client_id()

            try:
                if client_id not in self.active_sessions:
                    emit(
                        "error",
                        {"status": "error", "message": "No active session found"},
                    )
                    return

                if not self.active_sessions[client_id].get("configured"):
                    emit(
                        "error",
                        {"status": "error", "message": "Session not configured"},
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
                self.logger.error(f"Audio processing error: {str(e)}")
                emit("error", {"status": "error", "message": str(e)})

        @self.socketio.on("stop", namespace="/api/stt/stream")
        def handle_stop():
            client_id = self._get_client_id()

            if client_id in self.active_sessions:
                self.use_case.stop_streaming()
                self.active_sessions[client_id]["streaming"] = False
                self.logger.info(f"Streaming stopped for client {client_id}")
                emit("stopped", {"status": "stopped", "message": "Streaming stopped"})

    def transcribe_speech(self):
        return {"error": "Use streaming endpoint instead"}, 400

    def _get_client_id(self) -> str:
        try:
            return request.sid
        except Exception:
            return "unknown"

    def _start_streaming_thread(self, client_id: str, callback) -> None:
        try:
            if client_id in self.active_sessions:
                self.active_sessions[client_id]["streaming"] = True

                import asyncio

                try:

                    loop = asyncio.get_event_loop()
                    if loop.is_running():

                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                except RuntimeError:

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                try:

                    loop.run_until_complete(self.use_case.start_streaming(callback))
                except Exception as e:
                    self.logger.error(f"Error in streaming loop: {str(e)}")

                    callback({"type": "error", "message": f"Streaming error: {str(e)}"})
                finally:

                    if client_id in self.active_sessions:
                        self.active_sessions[client_id]["streaming"] = False
                    try:
                        loop.close()
                    except:
                        pass

        except Exception as e:
            self.logger.error(f"Streaming thread error: {str(e)}")
            if client_id in self.active_sessions:
                self.active_sessions[client_id]["streaming"] = False

            callback(
                {"type": "error", "message": f"Failed to start streaming: {str(e)}"}
            )


def register_routes(
    socketio: SocketIO, use_case: STTStreamingUseCase
) -> STTStreamingController:
    controller = STTStreamingController(socketio, use_case)
    return controller


def create_stt_streaming_blueprint(
    socketio: SocketIO, use_case: STTStreamingUseCase
) -> Blueprint:
    blueprint = Blueprint("stt_streaming", __name__)

    STTStreamingController(socketio, use_case)

    return blueprint
