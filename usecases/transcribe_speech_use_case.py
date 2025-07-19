from core.domain.stt_model import STTRequest, STTResponse
from core.interfaces.stt_domain_service_interface import STTDomainServiceInterface
from core.interfaces.use_case_interfaces import UseCaseInterface


class TranscribeSpeechUseCase(UseCaseInterface):
    def __init__(self, service: STTDomainServiceInterface) -> None:
        self.service = service

    def execute(self, request: STTRequest) -> STTResponse:
        return self.service.process_stt_request(request)
