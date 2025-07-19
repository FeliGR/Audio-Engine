from abc import ABC, abstractmethod
from core.domain.stt_model import STTRequest, STTResponse


class GoogleSTTClientInterface(ABC):
    @abstractmethod
    def transcribe_speech(self, request: STTRequest) -> STTResponse:
        raise NotImplementedError
