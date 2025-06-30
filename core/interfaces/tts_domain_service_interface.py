"""
TTS Domain Service Interface Module

This module defines the interface for TTS domain services that handle
the core business logic for text-to-speech operations.
"""

from abc import ABC, abstractmethod
from core.domain.tts_model import TTSRequest, TTSResponse


class TTSDomainServiceInterface(ABC):  
    """
    Interface for TTS domain services.

    This interface defines the contract for services that handle
    the core business logic of text-to-speech synthesis.
    """

    @abstractmethod
    def process_tts_request(self, request: TTSRequest) -> TTSResponse:
        """
        Process a TTS synthesis request.

        Args:
            request: TTS request containing text and voice configuration.

        Returns:
            TTSResponse containing synthesis result or error information.
        """
        raise NotImplementedError
