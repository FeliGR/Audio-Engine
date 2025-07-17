"""
STT Streaming Domain Models Module

This module defines the core domain models for streaming STT service,
including configuration structures and result models.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class STTStreamingConfig:
    """
    Configuration for streaming speech-to-text recognition.

    Attributes:
        encoding: Audio encoding format (e.g., "WEBM_OPUS", "LINEAR16").
        sample_rate_hertz: Audio sample rate in Hz.
        language_code: Language code for recognition (e.g., "en-US").
        interim_results: Whether to return interim results.
        single_utterance: Whether to detect single utterance.
        enable_word_time_offsets: Whether to include word-level timestamps.
        max_alternatives: Maximum number of recognition alternatives.
        enable_automatic_punctuation: Whether to enable automatic punctuation.
        model: Recognition model to use (e.g., "latest_long", "latest_short").
    """

    encoding: str = "WEBM_OPUS"
    sample_rate_hertz: int = 48000
    language_code: str = "en-US"
    interim_results: bool = True
    single_utterance: bool = False
    enable_word_time_offsets: bool = False
    max_alternatives: int = 1
    enable_automatic_punctuation: bool = True
    model: str = "latest_long"

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.sample_rate_hertz <= 0:
            raise ValueError("Sample rate must be positive")

        if self.max_alternatives < 1:
            raise ValueError("Max alternatives must be at least 1")

        valid_encodings = {"WEBM_OPUS", "LINEAR16", "FLAC", "OGG_OPUS", "AMR", "AMR_WB"}
        if self.encoding.upper() not in valid_encodings:
            raise ValueError(f"Unsupported encoding: {self.encoding}")


@dataclass
class STTStreamingResult:
    """
    Streaming speech-to-text recognition result.

    Attributes:
        result_type: Type of result ("interim", "final", "end_of_utterance", "error").
        transcript: Transcribed text.
        confidence: Confidence score (0.0 to 1.0).
        is_final: Whether this is a final result.
        word_timestamps: List of word-level timestamps.
        error_message: Error message if result_type is "error".
    """

    result_type: str
    transcript: Optional[str] = None
    confidence: Optional[float] = None
    is_final: bool = False
    word_timestamps: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate result after initialization."""
        valid_types = {"interim", "final", "end_of_utterance", "error"}
        if self.result_type not in valid_types:
            raise ValueError(f"Invalid result type: {self.result_type}")

        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class AudioChunk:
    """
    Audio data chunk for streaming processing.

    Attributes:
        data: Raw audio bytes.
        timestamp: Optional timestamp for the chunk.
        sequence_number: Optional sequence number for ordering.
    """

    data: bytes
    timestamp: Optional[float] = None
    sequence_number: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate audio chunk after initialization."""
        if not self.data:
            raise ValueError("Audio data cannot be empty")
