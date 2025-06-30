"""
Google TTS Client Interface Module

This module defines the interface for Google Cloud Text-to-Speech client
implementations that handle speech synthesis operations.
"""

from abc import ABC, abstractmethod
from core.domain.tts_model import TTSRequest, TTSResponse


class GoogleTTSClientInterface(ABC):  
    """
    Interface for Google TTS clients.

    This interface defines the contract for clients that interact
    with Google Cloud Text-to-Speech API for speech synthesis.
    """

    @abstractmethod
    def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        """
        Synthesize speech from text using Google Cloud TTS.

        Args:
            request: TTS request containing text and voice configuration.

        Returns:
            TTSResponse containing the synthesized audio or error information.
        """
        raise NotImplementedError
