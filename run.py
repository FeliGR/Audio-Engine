#!/usr/bin/env python3
"""
Entry point for running the TTS-Engine application.

This script provides a simple way to start the Flask application with SocketIO
support without using Gunicorn, which helps avoid async issues with Google APIs.
"""

from app import create_app
from app.extensions import get_socketio


def main():
    """Main entry point for the application."""
    app = create_app()
    socketio = get_socketio()

    # Run the application with SocketIO
    socketio.run(
        app,
        host=app.config.get("HOST", "0.0.0.0"),
        port=app.config.get("PORT", 5003),
        debug=app.config.get("DEBUG", False),
        allow_unsafe_werkzeug=True,  # Allow for development/production use
    )


if __name__ == "__main__":
    main()
