from abc import ABC, abstractmethod

from core.domain.tts_model import TTSRequest, TTSResponse


class TTSDomainServiceInterface(ABC):
    @abstractmethod
    def process_tts_request(self, request: TTSRequest) -> TTSResponse:

        raise NotImplementedError
