from abc import ABC, abstractmethod

from core.domain.stt_model import STTRequest, STTResponse


class STTDomainServiceInterface(ABC):
    @abstractmethod
    def process_stt_request(self, request: STTRequest) -> STTResponse:
        raise NotImplementedError
