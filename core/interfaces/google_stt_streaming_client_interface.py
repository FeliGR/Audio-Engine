from abc import ABC, abstractmethod
from typing import Any, Callable, Dict


class GoogleSTTStreamingClientInterface(ABC):
    @abstractmethod
    def setup_config(self, config_data: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_audio_chunk(self, audio_data: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    async def start_streaming(
        self, result_callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop_streaming(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_active(self) -> bool:
        raise NotImplementedError
