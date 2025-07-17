"""
STT Domain Service Interface Module

This module defines the interface for STT domain services that handle
the core business logic for speech-to-text operations.
"""

from abc import ABC, abstractmethod
from core.domain.stt_model import STTRequest, STTResponse


class STTDomainServiceInterface(ABC):
    """
    Interface for STT domain services.

    This interface defines the contract for services that handle
    the core business logic of speech-to-text transcription.
    """

    @abstractmethod
    def process_stt_request(self, request: STTRequest) -> STTResponse:
        """
        Process an STT transcription request.

        Args:
            request: STT request containing audio data and configuration.

        Returns:
            STTResponse containing transcription result or error information.
        """
        raise NotImplementedError
