import time

from flask import Flask, jsonify


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        return jsonify(
            {
                "status": "ok",
                "service": "tts-stt-service",
                "version": app.config.get("VERSION", "0.1.0"),
                "endpoints": {
                    "tts": "/api/tts",
                    "stt": "/api/stt",
                    "health": "/health",
                },
            }
        )

    @app.route("/health")
    def health():
        return jsonify({"status": "healthy", "timestamp": time.time()})
