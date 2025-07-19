from abc import ABC, abstractmethod


class STTControllerInterface(ABC):
    @abstractmethod
    def transcribe_speech(self):
        raise NotImplementedError
