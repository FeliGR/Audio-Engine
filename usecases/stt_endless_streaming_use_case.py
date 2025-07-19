from typing import Dict, Any, Callable

from adapters.clients.google_stt_endless_streaming_client import (
    GoogleSTTEndlessStreamingClient,
)
from adapters.loggers.logger_adapter import app_logger
from core.interfaces.use_case_interfaces import UseCaseInterface


class STTEndlessStreamingUseCase(UseCaseInterface):
    def __init__(self, client: GoogleSTTEndlessStreamingClient) -> None:
        self.client = client
        self.logger = app_logger

    def execute(self, request: Dict[str, Any]) -> None:
        try:
            self.client.setup_config(request)
            self.logger.info(
                "Endless STT streaming configuration executed successfully"
            )
        except Exception as e:
            self.logger.error("Failed to configure endless STT streaming: %s", e)
            raise

    def add_audio_data(self, audio_data: bytes) -> None:
        try:
            self.client.add_audio_chunk(audio_data)
        except Exception as e:
            self.logger.error("Failed to add audio data: %s", e)
            raise

    async def start_streaming(
        self, result_callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        try:
            await self.client.start_streaming(result_callback)
        except Exception as e:
            self.logger.error("Failed to start endless streaming: %s", e)
            raise

    def stop_streaming(self) -> None:
        try:
            self.client.stop_streaming()
            self.logger.info("Endless STT streaming stopped successfully")
        except Exception as e:
            self.logger.error("Failed to stop endless streaming: %s", e)
            raise

    def is_active(self) -> bool:
        return self.client.is_active()
