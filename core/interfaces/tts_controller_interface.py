from abc import ABC, abstractmethod


class TTSControllerInterface(ABC):
    @abstractmethod
    async def synthesize_speech(self):
        raise NotImplementedError
