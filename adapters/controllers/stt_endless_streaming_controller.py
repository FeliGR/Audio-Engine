"""
STT Endless Streaming Controller Module

This module provides the WebSocket controller for endless STT streaming endpoints.
It handles WebSocket connections, continuous audio streaming, and manages automatic
stream restarts for truly endless speech recognition.
"""

import threading
from typing import Dict, Any

from flask import Blueprint
from flask_socketio import SocketIO, emit
from marshmallow import Schema, fields, ValidationError

from adapters.loggers.logger_adapter import app_logger
from core.interfaces.stt_controller_interface import STTControllerInterface
from usecases.stt_endless_streaming_use_case import STTEndlessStreamingUseCase


class STTEndlessStreamingConfigSchema(Schema):
    """Schema for validating endless STT streaming configuration data."""

    encoding = fields.String(missing="LINEAR16")
    sampleRateHertz = fields.Integer(missing=16000)
    languageCode = fields.String(missing="en-US")
    interimResults = fields.Boolean(missing=True)
    enableWordTimeOffsets = fields.Boolean(missing=False)
    maxAlternatives = fields.Integer(missing=1)
    enableAutomaticPunctuation = fields.Boolean(missing=True)
    model = fields.String(missing="latest_long")


class STTEndlessStreamingController(STTControllerInterface):
    """
    STT Endless Streaming Controller implementation.

    Handles WebSocket connections for continuous speech-to-text streaming
    with automatic restarts to overcome the 4-minute Google Cloud limitation.
    """

    def __init__(
        self, socketio: SocketIO, use_case: STTEndlessStreamingUseCase
    ) -> None:
        """
        Initialize the endless STT streaming controller.

        Args:
            socketio: Flask-SocketIO instance for WebSocket handling.
            use_case: Endless STT streaming use case for business logic.
        """
        self.socketio = socketio
        self.use_case = use_case
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.schema = STTEndlessStreamingConfigSchema()
        self.logger = app_logger
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register WebSocket event handlers for endless streaming."""

        @self.socketio.on("connect", namespace="/api/stt/endless")
        def handle_connect(auth=None):
            """Handle client connection."""
            client_id = self._get_client_id()
            self.logger.info("Endless STT streaming client connected: %s", client_id)

            # Initialize session
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
            """Handle client disconnection with graceful cleanup."""
            try:
                client_id = self._get_client_id()

                if client_id in self.active_sessions:
                    # Stop the endless streaming session
                    self.use_case.stop_streaming()
                    # Remove session
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
                # Always remove session on error
                try:
                    client_id = self._get_client_id()
                    if client_id in self.active_sessions:
                        del self.active_sessions[client_id]
                except Exception:
                    pass

        @self.socketio.on("config", namespace="/api/stt/endless")
        def handle_config(data):
            """Handle endless streaming configuration."""
            client_id = self._get_client_id()

            try:
                # Validate configuration
                config_data = self.schema.load(data.get("config", {}))

                # Execute configuration
                self.use_case.execute(config_data)

                # Mark session as configured
                if client_id in self.active_sessions:
                    self.active_sessions[client_id]["configured"] = True

                    # Define async result callback for endless streaming
                    async def result_callback(result: Dict[str, Any]) -> None:
                        """Send result to client via Socket.IO."""
                        try:
                            event_type = result.get("type", "result")

                            # Map internal event types to client-friendly events
                            event_mapping = {
                                "streaming_started": "endless_started",
                                "stream_restart": "stream_restart",
                                "final_result": "final_result",
                                "interim_result": "interim_result",
                                "error": "error",
                                "fatal_error": "fatal_error",
                            }

                            client_event = event_mapping.get(event_type, event_type)

                            # Emit to the specific client
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

                    # Start endless streaming in a background thread
                    def start_endless_streaming():
                        """Start the endless streaming in a background thread."""
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
            """Handle incoming audio data for endless streaming."""
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

                # Process audio data
                audio_data = data.get("data")  # Frontend sends 'data' field
                if not audio_data:
                    emit(
                        "error",
                        {"status": "error", "message": "No audio data received"},
                    )
                    return

                # Convert array back to bytes
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

                # Pass audio to use case for endless processing
                self.use_case.add_audio_data(audio_bytes)

            except Exception as e:
                self.logger.error(f"Endless streaming audio processing error: {str(e)}")
                emit("error", {"status": "error", "message": str(e)})

        @self.socketio.on("stop", namespace="/api/stt/endless")
        def handle_stop():
            """Handle stop endless streaming request."""
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
            """Handle status request for endless streaming."""
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
        """Get the current client's session ID."""
        from flask import request

        return request.sid


def create_stt_endless_streaming_blueprint(
    socketio: SocketIO, use_case: STTEndlessStreamingUseCase
) -> Blueprint:
    """
    Create and configure the endless STT streaming blueprint.

    Args:
        socketio: Flask-SocketIO instance.
        use_case: Endless STT streaming use case instance.

    Returns:
        Blueprint: Configured endless streaming blueprint.
    """
    blueprint = Blueprint("stt_endless_streaming", __name__)
    controller = STTEndlessStreamingController(socketio, use_case)

    @blueprint.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint for endless streaming."""
        return {
            "status": "healthy",
            "service": "stt_endless_streaming",
            "message": "STT endless streaming service is running",
        }

    return blueprint
