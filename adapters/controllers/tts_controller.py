"""
TTS Controller Module

This module provides the Flask controller for TTS synthesis endpoints.
It handles request validation, voice configuration, and response formatting.
"""

from typing import Tuple, Dict, Any

from flask import Blueprint, request
from marshmallow import Schema, fields, ValidationError

from adapters.loggers.logger_adapter import app_logger
from app.api_response import ApiResponse
from core.domain.tts_model import TTSRequest, VoiceConfig
from core.interfaces.tts_controller_interface import TTSControllerInterface
from usecases.synthesize_speech_use_case import SynthesizeSpeechUseCase


class TTSRequestSchema(Schema):
    """Schema for validating TTS request data."""

    text = fields.String(required=True, validate=fields.Length(min=1, max=5000))
    voiceConfig = fields.Dict(keys=fields.String(), values=fields.Raw(), missing={})


class TTSController(TTSControllerInterface):
    """
    TTS Controller implementation.

    Handles HTTP requests for text-to-speech synthesis, including
    request validation and response formatting.
    """

    def __init__(self, use_case: SynthesizeSpeechUseCase) -> None:
        """
        Initialize the TTS controller.

        Args:
            use_case: The use case for speech synthesis.
        """
        self.use_case = use_case

    def synthesize_speech(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle TTS synthesis requests.

        Returns:
            Tuple containing the response data and HTTP status code.
        """
        try:
            data = request.get_json() or {}
            validated_data = TTSRequestSchema().load(data)

            voice_config_data = validated_data["voiceConfig"]
            voice_config = VoiceConfig(
                language_code=voice_config_data.get("languageCode", "en-US"),
                name=voice_config_data.get("name", "en-US-Wavenet-D"),
                ssml_gender=voice_config_data.get("ssmlGender", "NEUTRAL"),
                speaking_rate=voice_config_data.get("speakingRate", 1.0),
                pitch=voice_config_data.get("pitch", 0.0),
            )

            tts_request = TTSRequest(
                text=validated_data["text"], voice_config=voice_config
            )

            response = self.use_case.execute(tts_request)

            if response.success:
                return (
                    ApiResponse.success({"audioContent": response.audio_content}),
                    200,
                )

            app_logger.error("TTS synthesis failed: %s", response.error_message)
            return (
                ApiResponse.error(response.error_message or "TTS synthesis failed"),
                500,
            )

        except ValidationError as validation_error:
            app_logger.error("Request validation failed: %s", validation_error.messages)
            return (
                ApiResponse.error(
                    "Validation error", details=validation_error.messages
                ),
                400,
            )

        except RuntimeError as runtime_error:
            app_logger.error("Runtime error: %s", str(runtime_error), exc_info=True)
            return ApiResponse.error("Internal server error"), 500

        except (ValueError, TypeError) as processing_error:
            app_logger.error(
                "Processing error: %s", str(processing_error), exc_info=True
            )
            return ApiResponse.error("Request processing failed"), 400


def create_tts_blueprint(use_case: SynthesizeSpeechUseCase) -> Blueprint:
    """
    Create and configure the TTS blueprint.

    Args:
        use_case: The use case for speech synthesis.

    Returns:
        Configured Flask blueprint for TTS endpoints.
    """
    blueprint = Blueprint("tts", __name__, url_prefix="/api/tts")
    controller = TTSController(use_case)

    @blueprint.route("", methods=["POST"])
    def synthesize():
        """TTS synthesis endpoint."""
        return controller.synthesize_speech()

    return blueprint
