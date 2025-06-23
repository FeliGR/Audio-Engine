"""
Flask Application Factory Module for TTS-Engine.
"""

import os
from typing import Type
from flask import Flask

from adapters.clients.google_tts_client import GoogleTTSClient
from adapters.controllers.tts_controller import create_tts_blueprint
from adapters.loggers.logger_adapter import app_logger
from app.extensions import register_extensions
from app.handlers import (
    register_error_handlers,
    register_request_hooks,
    register_shutdown_handlers,
)
from app.routes import register_routes
from config import Config, DevelopmentConfig, ProductionConfig
from usecases.synthesize_speech_use_case import SynthesizeSpeechUseCase
from core.services.tts_domain_service import TTSDomainService


class ApplicationFactory:  # pylint: disable=too-few-public-methods
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
        google_client = GoogleTTSClient()
        tts_service = TTSDomainService(google_client)
        flask_app.synthesize_speech_use_case = SynthesizeSpeechUseCase(tts_service)

    @staticmethod
    def _register_blueprints(flask_app):
        """Register blueprints with the Flask application."""
        blueprint = create_tts_blueprint(flask_app.synthesize_speech_use_case)
        flask_app.register_blueprint(blueprint)


create_app = ApplicationFactory.create_app
app = create_app()

if __name__ == "__main__":
    app.run(
        host=app.config.get("HOST", "0.0.0.0"),
        port=app.config.get("PORT", 5003),
        debug=app.config.get("DEBUG", False),
    )
