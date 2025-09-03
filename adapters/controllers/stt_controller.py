from typing import Any, Dict, Tuple

from flask import Blueprint, request
from marshmallow import Schema, ValidationError, fields

from adapters.loggers.logger_adapter import app_logger
from app.api_response import ApiResponse
from core.domain.stt_model import STTRequest
from core.interfaces.stt_controller_interface import STTControllerInterface
from usecases.transcribe_speech_use_case import TranscribeSpeechUseCase


class STTRequestSchema(Schema):
    audio_data = fields.String(required=True, validate=fields.Length(min=1))
    format = fields.String(missing="webm")
    language = fields.String(missing="en-US")
    enable_word_timestamps = fields.Boolean(missing=False)
    sample_rate = fields.Integer(missing=48000)
    enable_automatic_punctuation = fields.Boolean(missing=True)
    model = fields.String(missing="latest_long")


class STTController(STTControllerInterface):
    def __init__(self, use_case: TranscribeSpeechUseCase) -> None:
        self.use_case = use_case

    def transcribe_speech(self) -> Tuple[Dict[str, Any], int]:
        try:
            data = request.get_json() or {}
            validated_data = STTRequestSchema().load(data)

            stt_request = STTRequest(
                audio_data=validated_data["audio_data"],
                format=validated_data["format"],
                language=validated_data["language"],
                enable_word_timestamps=validated_data["enable_word_timestamps"],
                sample_rate=validated_data["sample_rate"],
                enable_automatic_punctuation=validated_data[
                    "enable_automatic_punctuation"
                ],
                model=validated_data["model"],
            )

            response = self.use_case.execute(stt_request)

            if response.success:
                response_data = {
                    "transcription": response.transcription,
                    "confidence": response.confidence,
                }

                if response.word_timestamps:
                    response_data["word_timestamps"] = [
                        {
                            "word": wt.word,
                            "start_time": wt.start_time,
                            "end_time": wt.end_time,
                        }
                        for wt in response.word_timestamps
                    ]

                return (
                    ApiResponse.success(response_data, "Transcription successful"),
                    200,
                )

            app_logger.error("STT transcription failed: %s", response.error_message)
            return (
                ApiResponse.error(response.error_message or "STT transcription failed"),
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


def create_stt_blueprint(use_case: TranscribeSpeechUseCase) -> Blueprint:
    blueprint = Blueprint("stt", __name__, url_prefix="/api/stt")
    controller = STTController(use_case)

    @blueprint.route("", methods=["POST"])
    def transcribe():
        return controller.transcribe_speech()

    return blueprint
