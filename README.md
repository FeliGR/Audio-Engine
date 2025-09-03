# Audio Engine

A high-performance audio processing engine with text-to-speech and speech-to-text capabilities, featuring real-time streaming.

## Features

- **Text-to-Speech**: Convert text to natural speech with customizable voice parameters
- **Speech-to-Text**: Transcribe audio to text with multiple format support
- **Real-time Streaming**: Live audio transcription with WebSocket support
- **Endless Streaming**: Continuous speech recognition for long-form audio
- **Voice Configuration**: Multilingual TTS with adjustable speaking rate, pitch, and gender
- **Word Timestamps**: Precise timing information for transcribed words
- **Multi-format Audio**: Support for webm, wav, mp3, flac, and opus formats

## Quick Start

```bash
git clone https://github.com/your-username/Audio-Engine.git
cd Audio-Engine
pip install -r requirements.txt
python -m app
```

## Configuration

Create a `.env` file:

```env
DEBUG=False
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key_here
HOST=0.0.0.0
PORT=5003
CORS_ORIGINS=*
API_RATE_LIMIT=500
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json
```

### Google Cloud Setup

1. Create a Google Cloud project and enable the Text-to-Speech and Speech-to-Text APIs
2. Create a service account and download the JSON credentials file
3. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the file path

## Docker

```bash
docker-compose up -d
```

Make sure to place your Google Cloud credentials file as `audio-engine-key.json` in the project root.

## API Endpoints

### Health Check

```
GET /health
```

### Text-to-Speech

```
POST /api/tts
```

### Speech-to-Text

```
POST /api/stt
```

### WebSocket Events

- `stt_streaming`: Real-time speech transcription
- `stt_endless_streaming`: Continuous speech recognition

## Tech Stack

- Flask 2.3.3
- Flask-SocketIO 5.3.6
- Google Cloud TTS 2.16.3
- Google Cloud STT 2.21.0
- Marshmallow 3.20.1
- Eventlet 0.33.3
