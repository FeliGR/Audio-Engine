from abc import ABC, abstractmethod
from core.domain.tts_model import TTSRequest, TTSResponse


class GoogleTTSClientInterface(ABC):
    @abstractmethod
    def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        raise NotImplementedError
