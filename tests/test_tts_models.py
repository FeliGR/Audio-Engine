"""
Unit Tests for TTS Domain Models

This module contains comprehensive unit tests for the TTS domain models,
including validation, data consistency, and error handling tests.
"""

import pytest
from core.domain.tts_model import VoiceConfig, TTSRequest, TTSResponse


class TestVoiceConfig:
    """Test cases for VoiceConfig model."""

    def test_voice_config_valid_defaults(self):
        """Test VoiceConfig with valid default values."""
        config = VoiceConfig()
        assert config.language_code == "en-US"
        assert config.name == "en-US-Wavenet-D"
        assert config.ssml_gender == "NEUTRAL"
        assert config.speaking_rate == 1.0
        assert config.pitch == 0.0

    def test_voice_config_valid_custom_values(self):
        """Test VoiceConfig with valid custom values."""
        config = VoiceConfig(
            language_code="es-ES",
            name="es-ES-Wavenet-B",
            ssml_gender="FEMALE",
            speaking_rate=1.5,
            pitch=5.0,
        )
        assert config.language_code == "es-ES"
        assert config.name == "es-ES-Wavenet-B"
        assert config.ssml_gender == "FEMALE"
        assert config.speaking_rate == 1.5
        assert config.pitch == 5.0

    def test_voice_config_invalid_speaking_rate(self):
        """Test VoiceConfig with invalid speaking rate."""
        with pytest.raises(
            ValueError, match="Speaking rate must be between 0.25 and 4.0"
        ):
            VoiceConfig(speaking_rate=5.0)

        with pytest.raises(
            ValueError, match="Speaking rate must be between 0.25 and 4.0"
        ):
            VoiceConfig(speaking_rate=0.1)

    def test_voice_config_invalid_pitch(self):
        """Test VoiceConfig with invalid pitch."""
        with pytest.raises(ValueError, match="Pitch must be between -20.0 and 20.0"):
            VoiceConfig(pitch=25.0)

        with pytest.raises(ValueError, match="Pitch must be between -20.0 and 20.0"):
            VoiceConfig(pitch=-25.0)


class TestTTSRequest:
    """Test cases for TTSRequest model."""

    def test_tts_request_valid(self):
        """Test TTSRequest with valid data."""
        voice_config = VoiceConfig()
        request = TTSRequest(text="Hello, world!", voice_config=voice_config)
        assert request.text == "Hello, world!"
        assert request.voice_config == voice_config

    def test_tts_request_empty_text(self):
        """Test TTSRequest with empty text."""
        voice_config = VoiceConfig()
        with pytest.raises(ValueError, match="Text cannot be empty"):
            TTSRequest(text="", voice_config=voice_config)

        with pytest.raises(ValueError, match="Text cannot be empty"):
            TTSRequest(text="   ", voice_config=voice_config)

    def test_tts_request_text_too_long(self):
        """Test TTSRequest with text exceeding maximum length."""
        voice_config = VoiceConfig()
        long_text = "a" * 5001
        with pytest.raises(
            ValueError, match="Text exceeds maximum length of 5000 characters"
        ):
            TTSRequest(text=long_text, voice_config=voice_config)


class TestTTSResponse:
    """Test cases for TTSResponse model."""

    def test_tts_response_success(self):
        """Test TTSResponse for successful synthesis."""
        response = TTSResponse(audio_content="base64encodedaudio", success=True)
        assert response.audio_content == "base64encodedaudio"
        assert response.success is True
        assert response.error_message is None

    def test_tts_response_failure(self):
        """Test TTSResponse for failed synthesis."""
        response = TTSResponse(
            audio_content="", success=False, error_message="Synthesis failed"
        )
        assert response.audio_content == ""
        assert response.success is False
        assert response.error_message == "Synthesis failed"

    def test_tts_response_success_without_audio(self):
        """Test TTSResponse validation for success without audio content."""
        with pytest.raises(
            ValueError, match="Successful response must contain audio content"
        ):
            TTSResponse(audio_content="", success=True)

    def test_tts_response_failure_without_error(self):
        """Test TTSResponse validation for failure without error message."""
        with pytest.raises(
            ValueError, match="Failed response must contain error message"
        ):
            TTSResponse(audio_content="", success=False)
