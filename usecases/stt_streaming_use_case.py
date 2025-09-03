import asyncio
from typing import Any, Callable, Dict

from core.interfaces.google_stt_streaming_client_interface import (
    GoogleSTTStreamingClientInterface,
)
from core.interfaces.use_case_interfaces import UseCaseInterface


class STTStreamingUseCase(UseCaseInterface):
    def __init__(self, streaming_client: GoogleSTTStreamingClientInterface) -> None:
        self.streaming_client = streaming_client

    def execute(self, request: Dict[str, Any]) -> None:
        self.streaming_client.setup_config(request)

    async def start_streaming(
        self, result_callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        async def async_callback(result: Dict[str, Any]) -> None:
            if asyncio.iscoroutinefunction(result_callback):
                await result_callback(result)
            else:
                result_callback(result)

        await self.streaming_client.start_streaming(async_callback)

    def add_audio_data(self, audio_data: bytes) -> None:
        self.streaming_client.add_audio_chunk(audio_data)

    def stop_streaming(self) -> None:
        self.streaming_client.stop_streaming()

    def is_streaming_active(self) -> bool:
        return self.streaming_client.is_active()
