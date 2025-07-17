"""
STT Endless Streaming Use Case Module

This module provides the use case for endless speech-to-text streaming functionality.
It manages continuous streaming with automatic restarts and maintains audio buffering.
"""

from typing import Dict, Any, Callable

from adapters.clients.google_stt_endless_streaming_client import (
    GoogleSTTEndlessStreamingClient,
)
from adapters.loggers.logger_adapter import app_logger
from core.interfaces.use_case_interfaces import UseCaseInterface


class STTEndlessStreamingUseCase(UseCaseInterface):
    """
    Use case for endless STT streaming operations.

    This use case handles continuous speech recognition with automatic
    stream restarts to overcome Google Cloud's 4-minute limitation.
    """

    def __init__(self, client: GoogleSTTEndlessStreamingClient) -> None:
        """
        Initialize the endless streaming use case.

        Args:
            client: The endless streaming client implementation.
        """
        self.client = client
        self.logger = app_logger

    def execute(self, request: Dict[str, Any]) -> None:
        """
        Execute the configuration for endless streaming.

        Args:
            request: Configuration parameters for the streaming session.
        """
        try:
            self.client.setup_config(request)
            self.logger.info(
                "Endless STT streaming configuration executed successfully"
            )
        except Exception as e:
            self.logger.error("Failed to configure endless STT streaming: %s", e)
            raise

    def add_audio_data(self, audio_data: bytes) -> None:
        """
        Add audio data to the streaming buffer.

        Args:
            audio_data: Raw audio bytes to be processed.
        """
        try:
            self.client.add_audio_chunk(audio_data)
        except Exception as e:
            self.logger.error("Failed to add audio data: %s", e)
            raise

    async def start_streaming(
        self, result_callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Start the endless streaming recognition.

        Args:
            result_callback: Callback function to handle recognition results.
        """
        try:
            await self.client.start_streaming(result_callback)
        except Exception as e:
            self.logger.error("Failed to start endless streaming: %s", e)
            raise

    def stop_streaming(self) -> None:
        """Stop the endless streaming recognition."""
        try:
            self.client.stop_streaming()
            self.logger.info("Endless STT streaming stopped successfully")
        except Exception as e:
            self.logger.error("Failed to stop endless streaming: %s", e)
            raise

    def is_active(self) -> bool:
        """
        Check if the streaming is currently active.

        Returns:
            bool: True if streaming is active, False otherwise.
        """
        return self.client.is_active()
