"""
STT Domain Models Module

This module defines the core domain models for the STT service,
including request/response structures and audio configuration.
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class WordTimestamp:
    """
    Word timestamp information.

    Attributes:
        word: The word text.
        start_time: Start time in seconds.
        end_time: End time in seconds.
    """

    word: str
    start_time: float
    end_time: float


@dataclass
class STTRequest:
    """
    Request model for speech-to-text transcription.

    Attributes:
        audio_data: Base64-encoded audio content.
        format: Audio format (e.g., "webm", "wav", "mp3").
        language: Language code for recognition (e.g., "en-US").
        enable_word_timestamps: Whether to include word-level timestamps.
        sample_rate: Audio sample rate in Hz.
        enable_automatic_punctuation: Whether to enable automatic punctuation.
        model: Recognition model to use (e.g., "latest_long", "latest_short").
    """

    audio_data: str
    format: str = "webm"
    language: str = "en-US"
    enable_word_timestamps: bool = False
    sample_rate: int = 48000
    enable_automatic_punctuation: bool = True
    model: str = "latest_long"

    def __post_init__(self) -> None:
        """Validate STT request parameters."""
        if not self.audio_data.strip():
            raise ValueError("Audio data cannot be empty")
        if self.format not in ["webm", "wav", "mp3", "flac", "opus"]:
            raise ValueError(f"Unsupported audio format: {self.format}")
        if self.sample_rate < 8000 or self.sample_rate > 48000:
            raise ValueError("Sample rate must be between 8000 and 48000 Hz")


@dataclass
class STTResponse:
    """
    Response model for speech-to-text transcription.

    Attributes:
        transcription: The transcribed text.
        confidence: Confidence score (0.0 to 1.0).
        success: Indicates if the transcription was successful.
        error_message: Error message if transcription failed.
        word_timestamps: List of word-level timestamps (if requested).
    """

    transcription: str
    confidence: float
    success: bool
    error_message: Optional[str] = None
    word_timestamps: Optional[List[WordTimestamp]] = None

    def __post_init__(self) -> None:
        """Validate STT response consistency."""
        if self.success and not self.transcription:
            raise ValueError("Successful response must contain transcription")
        if not self.success and not self.error_message:
            raise ValueError("Failed response must contain error message")
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
