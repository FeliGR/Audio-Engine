"""
Transcribe Speech Use Case Module

This module implements the use case for speech transcription,
coordinating between the presentation and domain layers.
"""

from core.domain.stt_model import STTRequest, STTResponse
from core.interfaces.stt_domain_service_interface import STTDomainServiceInterface
from core.interfaces.use_case_interfaces import UseCaseInterface


class TranscribeSpeechUseCase(UseCaseInterface):
    """
    Use case for speech transcription.

    This use case coordinates the speech transcription workflow,
    delegating business logic to the domain service.
    """

    def __init__(self, service: STTDomainServiceInterface) -> None:
        """
        Initialize the speech transcription use case.

        Args:
            service: STT domain service implementation.
        """
        self.service = service

    def execute(self, request: STTRequest) -> STTResponse:
        """
        Execute speech transcription.

        Args:
            request: STT request containing audio data and configuration.

        Returns:
            STTResponse containing transcription result.
        """
        return self.service.process_stt_request(request)
