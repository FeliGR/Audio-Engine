from core.domain.exceptions import STTProcessingError, STTValidationError
from core.domain.stt_model import STTRequest, STTResponse
from core.interfaces.google_stt_client_interface import GoogleSTTClientInterface
from core.interfaces.stt_domain_service_interface import STTDomainServiceInterface


class STTDomainService(STTDomainServiceInterface):
    def __init__(self, google_client: GoogleSTTClientInterface) -> None:
        self.google_client = google_client

    def process_stt_request(self, request: STTRequest) -> STTResponse:
        try:

            self._validate_request(request)

            response = self.google_client.transcribe_speech(request)

            if not response.success and response.error_message:

                raise STTProcessingError(
                    f"Speech transcription failed: {response.error_message}"
                )

            return response

        except (STTValidationError, STTProcessingError) as stt_error:

            return STTResponse(
                transcription="",
                confidence=0.0,
                success=False,
                error_message=str(stt_error),
            )

        except (ValueError, TypeError, AttributeError) as e:

            return STTResponse(
                transcription="",
                confidence=0.0,
                success=False,
                error_message=f"Processing error during STT transcription: {str(e)}",
            )

        except (OSError, IOError, RuntimeError) as system_error:

            return STTResponse(
                transcription="",
                confidence=0.0,
                success=False,
                error_message=f"System error during STT processing: {str(system_error)}",
            )

    def _validate_request(self, request: STTRequest) -> None:
        if not request.audio_data.strip():
            raise STTValidationError("Audio data cannot be empty")

        if request.format.lower() not in ["webm", "wav", "mp3", "flac", "opus"]:
            raise STTValidationError(f"Unsupported audio format: {request.format}")

        if request.sample_rate < 8000 or request.sample_rate > 48000:
            raise STTValidationError("Sample rate must be between 8000 and 48000 Hz")

        if not request.language:
            raise STTValidationError("Language code is required")

        if request.model not in ["latest_long", "latest_short", "phone_call", "video"]:
            raise STTValidationError(f"Unsupported recognition model: {request.model}")
