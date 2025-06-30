"""
TTS Domain Service Module

This module implements the core business logic for TTS processing,
including validation, error handling, and client coordination.
"""

from core.domain.exceptions import TTSProcessingError, TTSValidationError
from core.domain.tts_model import TTSRequest, TTSResponse
from core.interfaces.google_tts_client_interface import GoogleTTSClientInterface
from core.interfaces.tts_domain_service_interface import TTSDomainServiceInterface


class TTSDomainService(
    TTSDomainServiceInterface
):  
    """
    Domain service for TTS processing.

    This service encapsulates the core business logic for text-to-speech
    synthesis, including request validation and error handling.
    """

    def __init__(self, google_client: GoogleTTSClientInterface) -> None:
        """
        Initialize the TTS domain service.

        Args:
            google_client: Google TTS client implementation.
        """
        self.google_client = google_client

    def process_tts_request(self, request: TTSRequest) -> TTSResponse:
        """
        Process a TTS synthesis request.

        Args:
            request: TTS request containing text and voice configuration.

        Returns:
            TTSResponse containing synthesis result or error information.
        """
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
        """
        Validate TTS request parameters.

        Args:
            request: TTS request to validate.

        Raises:
            TTSValidationError: If validation fails.
        """
        if not request.text.strip():
            raise TTSValidationError("Text cannot be empty")

        if len(request.text) > 5000:
            raise TTSValidationError("Text exceeds maximum length of 5000 characters")

        
        if not request.voice_config.language_code:
            raise TTSValidationError("Language code is required")

        if not request.voice_config.name:
            raise TTSValidationError("Voice name is required")
