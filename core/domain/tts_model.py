from dataclasses import dataclass
from typing import Optional


@dataclass
class VoiceConfig:
    language_code: str = "en-US"
    name: str = "en-US-Wavenet-D"
    ssml_gender: str = "NEUTRAL"
    speaking_rate: float = 1.0
    pitch: float = 0.0

    def __post_init__(self) -> None:
        if not 0.25 <= self.speaking_rate <= 4.0:
            raise ValueError("Speaking rate must be between 0.25 and 4.0")
        if not -20.0 <= self.pitch <= 20.0:
            raise ValueError("Pitch must be between -20.0 and 20.0")


@dataclass
class TTSRequest:
    text: str
    voice_config: VoiceConfig

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Text cannot be empty")
        if len(self.text) > 5000:
            raise ValueError("Text exceeds maximum length of 5000 characters")


@dataclass
class TTSResponse:
    audio_content: str
    success: bool
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        if self.success and not self.audio_content:
            raise ValueError("Successful response must contain audio content")
        if not self.success and not self.error_message:
            raise ValueError("Failed response must contain error message")
