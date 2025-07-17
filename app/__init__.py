"""
Flask Application Factory Module for TTS-Engine.
"""

import os
from typing import Type
from flask import Flask

from adapters.clients.google_tts_client import GoogleTTSClient
from adapters.clients.google_stt_client import GoogleSTTClient
from adapters.clients.google_stt_streaming_client import GoogleSTTStreamingClient
from adapters.clients.google_stt_endless_streaming_client import (
    GoogleSTTEndlessStreamingClient,
)
from adapters.controllers.tts_controller import create_tts_blueprint
from adapters.controllers.stt_controller import create_stt_blueprint
from adapters.controllers.stt_streaming_controller import create_stt_streaming_blueprint
from adapters.loggers.logger_adapter import app_logger
from app.extensions import register_extensions, get_socketio
from app.handlers import (
    register_error_handlers,
    register_request_hooks,
    register_shutdown_handlers,
)
from app.routes import register_routes
from config import Config, DevelopmentConfig, ProductionConfig
from usecases.synthesize_speech_use_case import SynthesizeSpeechUseCase
from usecases.transcribe_speech_use_case import TranscribeSpeechUseCase
from usecases.stt_streaming_use_case import STTStreamingUseCase
from usecases.stt_endless_streaming_use_case import STTEndlessStreamingUseCase
from core.services.tts_domain_service import TTSDomainService
from core.services.stt_domain_service import STTDomainService


class ApplicationFactory:
    """
    Factory class for creating and configuring Flask application instances.

    This class provides static methods to create a properly configured Flask
    application with all necessary extensions, blueprints, and use cases registered.
    """

    @staticmethod
    def create_app(config_class: Type[Config] = None) -> Flask:
        """
        Create and configure a Flask application instance.

        Args:
            config_class: Configuration class to use. If None, will be determined
                         based on FLASK_ENV environment variable.

        Returns:
            Flask: Configured Flask application instance.
        """
        if config_class is None:
            env = os.environ.get("FLASK_ENV", "development").lower()
            cfg_map = {
                "development": DevelopmentConfig,
                "production": ProductionConfig,
            }
            config_class = cfg_map.get(env, DevelopmentConfig)

        flask_app = Flask(__name__)
        flask_app.config.from_object(config_class)

        register_extensions(flask_app)
        ApplicationFactory._register_use_cases(flask_app)
        ApplicationFactory._register_blueprints(flask_app)
        register_error_handlers(flask_app)
        register_request_hooks(flask_app)
        register_shutdown_handlers(flask_app)
        register_routes(flask_app)

        app_logger.info(
            "TTS-Engine started in %s mode", os.environ.get("FLASK_ENV", "development")
        )
        return flask_app

    @staticmethod
    def _register_use_cases(flask_app):
        """Register use cases and dependencies with the Flask application."""

        google_tts_client = GoogleTTSClient()
        tts_service = TTSDomainService(google_tts_client)
        flask_app.synthesize_speech_use_case = SynthesizeSpeechUseCase(tts_service)

        google_stt_client = GoogleSTTClient()
        stt_service = STTDomainService(google_stt_client)
        flask_app.transcribe_speech_use_case = TranscribeSpeechUseCase(stt_service)

        # Setup streaming STT use case with endless streaming client
        google_stt_endless_streaming_client = GoogleSTTEndlessStreamingClient()
        flask_app.stt_streaming_use_case = STTStreamingUseCase(
            google_stt_endless_streaming_client
        )

        # Keep the original endless streaming use case for comparison/testing
        google_stt_original_streaming_client = GoogleSTTStreamingClient()
        flask_app.stt_original_streaming_use_case = STTStreamingUseCase(
            google_stt_original_streaming_client
        )

    @staticmethod
    def _register_blueprints(flask_app):
        """Register blueprints with the Flask application."""

        tts_blueprint = create_tts_blueprint(flask_app.synthesize_speech_use_case)
        flask_app.register_blueprint(tts_blueprint)

        stt_blueprint = create_stt_blueprint(flask_app.transcribe_speech_use_case)
        flask_app.register_blueprint(stt_blueprint)

        # Register streaming STT blueprint (now with endless streaming)
        socketio = get_socketio()
        stt_streaming_blueprint = create_stt_streaming_blueprint(
            socketio, flask_app.stt_streaming_use_case
        )
        flask_app.register_blueprint(stt_streaming_blueprint)

        # Register original streaming STT blueprint for comparison (optional)
        # stt_original_streaming_blueprint = create_stt_streaming_blueprint(
        #     socketio, flask_app.stt_original_streaming_use_case
        # )
        # flask_app.register_blueprint(stt_original_streaming_blueprint, url_prefix='/api/stt/original')


create_app = ApplicationFactory.create_app
app = create_app()

if __name__ == "__main__":
    socketio_instance = get_socketio()
    socketio_instance.run(
        app,
        host=app.config.get("HOST", "0.0.0.0"),
        port=app.config.get("PORT", 5003),
        debug=app.config.get("DEBUG", False),
    )
