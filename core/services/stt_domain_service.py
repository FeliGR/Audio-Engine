"""
STT Domain Service Module

This module implements the core business logic for STT processing,
including validation, error handling, and client coordination.
"""

from core.domain.exceptions import STTProcessingError, STTValidationError
from core.domain.stt_model import STTRequest, STTResponse
from core.interfaces.google_stt_client_interface import GoogleSTTClientInterface
from core.interfaces.stt_domain_service_interface import STTDomainServiceInterface


class STTDomainService(
    STTDomainServiceInterface
):  
    """
    Domain service for STT processing.

    This service encapsulates the core business logic for speech-to-text
    transcription, including request validation and error handling.
    """

    def __init__(self, google_client: GoogleSTTClientInterface) -> None:
        """
        Initialize the STT domain service.

        Args:
            google_client: Google STT client implementation.
        """
        self.google_client = google_client

    def process_stt_request(self, request: STTRequest) -> STTResponse:
        """
        Process an STT transcription request.

        Args:
            request: STT request containing audio data and configuration.

        Returns:
            STTResponse containing transcription result or error information.
        """
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
        """
        Validate STT request parameters.

        Args:
            request: STT request to validate.

        Raises:
            STTValidationError: If validation fails.
        """
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
