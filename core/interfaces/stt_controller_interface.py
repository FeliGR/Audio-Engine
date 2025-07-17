"""
STT Controller Interface Module

This module defines the interface for STT controllers that handle
HTTP requests for speech-to-text operations.
"""

from abc import ABC, abstractmethod


class STTControllerInterface(ABC):
    """
    Interface for STT controllers.

    This interface defines the contract for controllers that handle
    HTTP requests for speech-to-text transcription operations.
    """

    @abstractmethod
    def transcribe_speech(self):
        """
        Handle STT transcription requests.

        Returns:
            Tuple containing the response data and HTTP status code.
        """
        raise NotImplementedError
