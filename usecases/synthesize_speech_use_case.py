from core.domain.tts_model import TTSRequest, TTSResponse
from core.interfaces.tts_domain_service_interface import TTSDomainServiceInterface
from core.interfaces.use_case_interfaces import UseCaseInterface


class SynthesizeSpeechUseCase(UseCaseInterface):
    def __init__(self, service: TTSDomainServiceInterface) -> None:
        self.service = service

    def execute(self, request: TTSRequest) -> TTSResponse:
        return self.service.process_tts_request(request)
