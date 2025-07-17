"""
Google STT Streaming Client Interface Module

This module defines the interface for Google Cloud Speech-to-Text streaming client
implementations that handle real-time speech recognition operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable


class GoogleSTTStreamingClientInterface(ABC):
    """
    Interface for Google STT streaming clients.

    This interface defines the contract for clients that interact
    with Google Cloud Speech-to-Text streaming API for real-time speech recognition.
    """

    @abstractmethod
    def setup_config(self, config_data: Dict[str, Any]) -> None:
        """
        Setup streaming configuration.

        Args:
            config_data: Configuration dictionary containing audio and recognition settings.
        """
        raise NotImplementedError

    @abstractmethod
    def add_audio_chunk(self, audio_data: bytes) -> None:
        """
        Add audio chunk to the processing queue.

        Args:
            audio_data: Raw audio bytes to be processed.
        """
        raise NotImplementedError

    @abstractmethod
    async def start_streaming(
        self, result_callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Start streaming speech recognition.

        Args:
            result_callback: Async function to call with recognition results.
        """
        raise NotImplementedError

    @abstractmethod
    def stop_streaming(self) -> None:
        """Stop the streaming recognition."""
        raise NotImplementedError

    @abstractmethod
    def is_active(self) -> bool:
        """
        Check if streaming is currently active.

        Returns:
            bool: True if streaming is active, False otherwise.
        """
        raise NotImplementedError
