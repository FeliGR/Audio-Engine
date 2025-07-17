"""
STT Streaming Controller Module

This module provides the WebSocket controller for real-time STT streaming endpoints.
It handles WebSocket connections, audio streaming, and real-time transcription results.
"""

import threading
from typing import Dict, Any

from flask import request, Blueprint
from flask_socketio import SocketIO, emit
from marshmallow import Schema, fields, ValidationError

from adapters.loggers.logger_adapter import app_logger
from core.interfaces.stt_controller_interface import STTControllerInterface
from usecases.stt_streaming_use_case import STTStreamingUseCase


class STTStreamingConfigSchema(Schema):
    """Schema for validating STT streaming configuration data."""

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
    """
    STT Streaming Controller implementation.

    Handles WebSocket connections for real-time speech-to-text streaming,
    including configuration, audio data processing, and result broadcasting.
    """

    def __init__(self, socketio: SocketIO, use_case: STTStreamingUseCase) -> None:
        """
        Initialize the STT streaming controller.

        Args:
            socketio: Flask-SocketIO instance for WebSocket handling.
            use_case: STT streaming use case for business logic.
        """
        self.socketio = socketio
        self.use_case = use_case
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.schema = STTStreamingConfigSchema()
        self.logger = app_logger
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register WebSocket event handlers."""

        @self.socketio.on("connect", namespace="/api/stt/stream")
        def handle_connect(auth=None):
            """Handle client connection."""
            client_id = self._get_client_id()
            self.logger.info("STT streaming client connected: %s", client_id)

            # Initialize session
            self.active_sessions[client_id] = {"configured": False, "streaming": False}

            emit("connected", {"status": "connected", "message": "Ready for streaming"})

        @self.socketio.on("disconnect", namespace="/api/stt/stream")
        def handle_disconnect():
            """Handle client disconnection with graceful cleanup."""
            try:
                client_id = self._get_client_id()

                if client_id in self.active_sessions:
                    # Stop the streaming session
                    self.use_case.stop_streaming()  # Fixed: removed client_id argument
                    # Remove session
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
                # Always remove session on error
                try:
                    client_id = self._get_client_id()
                    if client_id in self.active_sessions:
                        del self.active_sessions[client_id]
                except Exception:
                    pass

        @self.socketio.on("config", namespace="/api/stt/stream")
        def handle_config(data):
            """Handle streaming configuration."""
            client_id = self._get_client_id()

            try:
                # Validate configuration
                config_data = self.schema.load(data.get("config", {}))

                # Execute configuration
                self.use_case.execute(config_data)

                # Mark session as configured
                if client_id in self.active_sessions:
                    self.active_sessions[client_id]["configured"] = True

                    # Start streaming with callback that emits to Socket.IO
                    def result_callback(result: Dict[str, Any]) -> None:
                        """Send result to client via Socket.IO."""
                        try:
                            event_type = result.get("type", "result")
                            # Use the socketio instance to emit to the specific client
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

                    # Start streaming in a background thread
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
            """Handle incoming audio data."""
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

                # Pass audio to use case for processing
                self.use_case.add_audio_data(audio_bytes)

            except Exception as e:
                self.logger.error(f"Audio processing error: {str(e)}")
                emit("error", {"status": "error", "message": str(e)})

        @self.socketio.on("stop", namespace="/api/stt/stream")
        def handle_stop():
            """Handle stop streaming request."""
            client_id = self._get_client_id()

            if client_id in self.active_sessions:
                self.use_case.stop_streaming()  # Fixed: removed client_id argument
                self.active_sessions[client_id]["streaming"] = False
                self.logger.info(f"Streaming stopped for client {client_id}")
                emit("stopped", {"status": "stopped", "message": "Streaming stopped"})

    def transcribe_speech(self):
        """Handle STT transcription requests (not used for streaming)."""
        return {"error": "Use streaming endpoint instead"}, 400

    def _get_client_id(self) -> str:
        """Get the client ID from the current request context."""
        try:
            return request.sid
        except Exception:
            return "unknown"

    def _start_streaming_thread(self, client_id: str, callback) -> None:
        """Start streaming in a background thread."""
        try:
            if client_id in self.active_sessions:
                self.active_sessions[client_id]["streaming"] = True

                # Create a proper event loop for this thread
                import asyncio

                try:
                    # Try to get the current loop
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If the loop is running, we need a new one for this thread
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                except RuntimeError:
                    # No loop in this thread, create one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                try:
                    # Run the streaming in the event loop
                    loop.run_until_complete(self.use_case.start_streaming(callback))
                except Exception as e:
                    self.logger.error(f"Error in streaming loop: {str(e)}")
                    # Send error via callback (Socket.IO)
                    callback({"type": "error", "message": f"Streaming error: {str(e)}"})
                finally:
                    # Clean up
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
            # Send error via callback (Socket.IO)
            callback(
                {"type": "error", "message": f"Failed to start streaming: {str(e)}"}
            )


def register_routes(
    socketio: SocketIO, use_case: STTStreamingUseCase
) -> STTStreamingController:
    """
    Register STT streaming routes.

    Args:
        socketio: Flask-SocketIO instance.
        use_case: STT streaming use case.

    Returns:
        The STT streaming controller instance.
    """
    controller = STTStreamingController(socketio, use_case)
    return controller


def create_stt_streaming_blueprint(
    socketio: SocketIO, use_case: STTStreamingUseCase
) -> Blueprint:
    """
    Create STT streaming blueprint with WebSocket support.

    Args:
        socketio: Flask-SocketIO instance.
        use_case: STT streaming use case.

    Returns:
        Blueprint: Configured blueprint for STT streaming.
    """
    blueprint = Blueprint("stt_streaming", __name__)

    # Initialize controller with SocketIO and use case
    STTStreamingController(socketio, use_case)

    @blueprint.route("/api/stt/stream/info", methods=["GET"])
    def stream_info():
        """Get streaming endpoint information."""
        return {
            "endpoint": "/api/stt/stream",
            "protocol": "WebSocket",
            "events": {
                "config": "Send streaming configuration",
                "audio": "Send audio data chunks",
                "stop": "Stop streaming",
                "interim_result": "Receive interim transcription",
                "final_result": "Receive final transcription",
                "end_of_utterance": "End of speech detected",
                "error": "Error messages",
            },
            "sample_config": {
                "encoding": "WEBM_OPUS",
                "sampleRateHertz": 48000,
                "languageCode": "en-US",
                "interimResults": True,
                "singleUtterance": False,
                "enableWordTimeOffsets": False,
                "maxAlternatives": 1,
                "enableAutomaticPunctuation": True,
                "model": "latest_long",
            },
        }

    return blueprint
