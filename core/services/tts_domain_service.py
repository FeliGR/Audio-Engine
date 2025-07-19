from core.domain.exceptions import TTSProcessingError, TTSValidationError
from core.domain.tts_model import TTSRequest, TTSResponse
from core.interfaces.google_tts_client_interface import GoogleTTSClientInterface
from core.interfaces.tts_domain_service_interface import TTSDomainServiceInterface


class TTSDomainService(TTSDomainServiceInterface):
    def __init__(self, google_client: GoogleTTSClientInterface) -> None:
        self.google_client = google_client

    def process_tts_request(self, request: TTSRequest) -> TTSResponse:
        try:

            self._validate_request(request)

            response = self.google_client.synthesize_speech(request)

            if not response.success and response.error_message:

                raise TTSProcessingError(
                    f"Speech synthesis failed: {response.error_message}"
                )

            return response

        except (TTSValidationError, TTSProcessingError) as tts_error:

            return TTSResponse(
                audio_content="",
                success=False,
                error_message=str(tts_error),
            )

        except (ValueError, TypeError, AttributeError) as e:

            return TTSResponse(
                audio_content="",
                success=False,
                error_message=f"Processing error during TTS synthesis: {str(e)}",
            )

        except (OSError, IOError, RuntimeError) as system_error:

            return TTSResponse(
                audio_content="",
                success=False,
                error_message=f"System error during TTS processing: {str(system_error)}",
            )

    def _validate_request(self, request: TTSRequest) -> None:
        if not request.text.strip():
            raise TTSValidationError("Text cannot be empty")

        if len(request.text) > 5000:
            raise TTSValidationError("Text exceeds maximum length of 5000 characters")

        if not request.voice_config.language_code:
            raise TTSValidationError("Language code is required")

        if not request.voice_config.name:
            raise TTSValidationError("Voice name is required")
