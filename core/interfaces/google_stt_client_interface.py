"""
Google STT Client Interface Module

This module defines the interface for Google Cloud Speech-to-Text client
implementations that handle speech recognition operations.
"""

from abc import ABC, abstractmethod
from core.domain.stt_model import STTRequest, STTResponse


class GoogleSTTClientInterface(ABC):  
    """
    Interface for Google STT clients.

    This interface defines the contract for clients that interact
    with Google Cloud Speech-to-Text API for speech recognition.
    """

    @abstractmethod
    def transcribe_speech(self, request: STTRequest) -> STTResponse:
        """
        Transcribe speech from audio using Google Cloud STT.

        Args:
            request: STT request containing audio data and configuration.

        Returns:
            STTResponse containing the transcription or error information.
        """
        raise NotImplementedError
