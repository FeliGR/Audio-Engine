"""
Synthesize Speech Use Case Module

This module implements the use case for speech synthesis,
coordinating between the presentation and domain layers.
"""

from core.domain.tts_model import TTSRequest, TTSResponse
from core.interfaces.tts_domain_service_interface import TTSDomainServiceInterface
from core.interfaces.use_case_interfaces import UseCaseInterface


class SynthesizeSpeechUseCase(
    UseCaseInterface
):  
    """
    Use case for speech synthesis.

    This use case coordinates the speech synthesis workflow,
    delegating business logic to the domain service.
    """

    def __init__(self, service: TTSDomainServiceInterface) -> None:
        """
        Initialize the speech synthesis use case.

        Args:
            service: TTS domain service implementation.
        """
        self.service = service

    def execute(self, request: TTSRequest) -> TTSResponse:
        """
        Execute speech synthesis.

        Args:
            request: TTS request containing text and voice configuration.

        Returns:
            TTSResponse containing synthesis result.
        """
        return self.service.process_tts_request(request)
