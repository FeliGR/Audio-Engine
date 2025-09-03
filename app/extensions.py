from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

from adapters.loggers.logger_adapter import app_logger

socketio = SocketIO(async_mode="threading")


def register_extensions(app: Flask) -> None:
    if not app.config["TESTING"]:

        cors_origins = app.config.get("CORS_ORIGINS", "*")
        if cors_origins == "*":

            cors_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
            ]

        CORS(
            app,
            resources={
                r"/api/*": {
                    "origins": cors_origins,
                    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                    "allow_headers": ["Content-Type", "Authorization", "Accept"],
                    "supports_credentials": True,
                },
                r"/health": {"origins": cors_origins, "methods": ["GET", "OPTIONS"]},
                r"/": {"origins": cors_origins, "methods": ["GET", "OPTIONS"]},
            },
            supports_credentials=True,
        )

        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri="memory://",
            default_limits=app.config.get(
                "DEFAULT_RATE_LIMITS", ["1000 per day", "500 per minute"]
            ),
        )
        limiter.init_app(app)

    socketio_cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    if app.config.get("CORS_ORIGINS") and app.config["CORS_ORIGINS"] != "*":
        socketio_cors_origins = app.config["CORS_ORIGINS"]

    socketio.init_app(
        app, cors_allowed_origins=socketio_cors_origins, async_mode="threading"
    )

    app_logger.debug("Extensions registered")


def get_socketio() -> SocketIO:
    return socketio
