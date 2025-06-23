"""
TTS Domain Models Module

This module defines the core domain models for the TTS service,
including request/response structures and voice configuration.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VoiceConfig:
    """
    Configuration for voice synthesis parameters.

    Attributes:
        language_code: Language code for the voice (e.g., "en-US").
        name: Specific voice name (e.g., "en-US-Wavenet-D").
        ssml_gender: SSML gender specification.
        speaking_rate: Speech rate multiplier (0.25 to 4.0).
        pitch: Voice pitch adjustment (-20.0 to 20.0).
    """

    language_code: str = "en-US"
    name: str = "en-US-Wavenet-D"
    ssml_gender: str = "NEUTRAL"
    speaking_rate: float = 1.0
    pitch: float = 0.0

    def __post_init__(self) -> None:
        """Validate voice configuration parameters."""
        if not 0.25 <= self.speaking_rate <= 4.0:
            raise ValueError("Speaking rate must be between 0.25 and 4.0")
        if not -20.0 <= self.pitch <= 20.0:
            raise ValueError("Pitch must be between -20.0 and 20.0")


@dataclass
class TTSRequest:
    """
    Request model for text-to-speech synthesis.

    Attributes:
        text: Text content to be synthesized.
        voice_config: Voice configuration parameters.
    """

    text: str
    voice_config: VoiceConfig

    def __post_init__(self) -> None:
        """Validate TTS request parameters."""
        if not self.text.strip():
            raise ValueError("Text cannot be empty")
        if len(self.text) > 5000:
            raise ValueError("Text exceeds maximum length of 5000 characters")


@dataclass
class TTSResponse:
    """
    Response model for text-to-speech synthesis.

    Attributes:
        audio_content: Base64-encoded audio content.
        success: Indicates if the synthesis was successful.
        error_message: Error message if synthesis failed.
    """

    audio_content: str
    success: bool
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate TTS response consistency."""
        if self.success and not self.audio_content:
            raise ValueError("Successful response must contain audio content")
        if not self.success and not self.error_message:
            raise ValueError("Failed response must contain error message")
