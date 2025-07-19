from app import create_app
from app.extensions import get_socketio


def main():
    app = create_app()
    
    socketio = get_socketio()

    socketio.run(
        app,
        host=app.config.get("HOST", "0.0.0.0"),
        port=app.config.get("PORT", 5003),
        debug=app.config.get("DEBUG", False),
        allow_unsafe_werkzeug=True,
    )


if __name__ == "__main__":
    main()
