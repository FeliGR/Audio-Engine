"""
STT Streaming Use Case Module

This module implements the use case for real-time speech transcription streaming,
coordinating between WebSocket connections and domain services.
"""

import asyncio
from typing import Dict, Any, Callable

from core.domain.stt_streaming_model import STTStreamingConfig, AudioChunk
from core.interfaces.google_stt_streaming_client_interface import (
    GoogleSTTStreamingClientInterface,
)
from core.interfaces.use_case_interfaces import UseCaseInterface


class STTStreamingUseCase(UseCaseInterface):
    """
    Use case for streaming speech transcription.

    This use case coordinates real-time speech transcription workflow,
    managing streaming connections and audio processing.
    """

    def __init__(self, streaming_client: GoogleSTTStreamingClientInterface) -> None:
        """
        Initialize the streaming STT use case.

        Args:
            streaming_client: Google STT streaming client implementation.
        """
        self.streaming_client = streaming_client

    def execute(self, request: Dict[str, Any]) -> None:
        """
        Execute streaming configuration setup.

        Args:
            request: Configuration data for streaming setup.
        """
        self.streaming_client.setup_config(request)

    async def start_streaming(
        self, result_callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Start streaming recognition.

        Args:
            result_callback: Function to call with recognition results.
        """

        # Create async wrapper for the callback if it's not async
        async def async_callback(result: Dict[str, Any]) -> None:
            if asyncio.iscoroutinefunction(result_callback):
                await result_callback(result)
            else:
                result_callback(result)

        await self.streaming_client.start_streaming(async_callback)

    def add_audio_data(self, audio_data: bytes) -> None:
        """
        Add audio data to processing queue.

        Args:
            audio_data: Raw audio bytes.
        """
        self.streaming_client.add_audio_chunk(audio_data)

    def stop_streaming(self) -> None:
        """Stop streaming recognition."""
        self.streaming_client.stop_streaming()

    def is_streaming_active(self) -> bool:
        """
        Check if streaming is currently active.

        Returns:
            bool: True if streaming is active.
        """
        return self.streaming_client.is_active()
