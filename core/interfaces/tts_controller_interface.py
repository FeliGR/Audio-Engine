"""
TTS Controller Interface Module

This module defines the interface for TTS controllers that handle
HTTP requests for text-to-speech operations.
"""

from abc import ABC, abstractmethod


class TTSControllerInterface(ABC):  
    """
    Interface for TTS controllers.

    This interface defines the contract for controllers that handle
    HTTP requests for text-to-speech synthesis operations.
    """

    @abstractmethod
    async def synthesize_speech(self):
        """
        Handle TTS synthesis requests.

        Returns:
            Tuple containing the response data and HTTP status code.
        """
        raise NotImplementedError
