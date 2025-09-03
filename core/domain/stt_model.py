from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WordTimestamp:
    word: str
    start_time: float
    end_time: float


@dataclass
class STTRequest:
    audio_data: str
    format: str = "webm"
    language: str = "en-US"
    enable_word_timestamps: bool = False
    sample_rate: int = 48000
    enable_automatic_punctuation: bool = True
    model: str = "latest_long"

    def __post_init__(self) -> None:
        if not self.audio_data.strip():
            raise ValueError("Audio data cannot be empty")
        if self.format not in ["webm", "wav", "mp3", "flac", "opus"]:
            raise ValueError(f"Unsupported audio format: {self.format}")
        if self.sample_rate < 8000 or self.sample_rate > 48000:
            raise ValueError("Sample rate must be between 8000 and 48000 Hz")


@dataclass
class STTResponse:
    transcription: str
    confidence: float
    success: bool
    error_message: Optional[str] = None
    word_timestamps: Optional[List[WordTimestamp]] = None

    def __post_init__(self) -> None:
        if self.success and not self.transcription:
            raise ValueError("Successful response must contain transcription")
        if not self.success and not self.error_message:
            raise ValueError("Failed response must contain error message")
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
