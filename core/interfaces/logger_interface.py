from abc import ABC, abstractmethod


class ILogger(ABC):
    @abstractmethod
    def debug(self, message: str, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def info(self, message: str, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    def error(self, message: str, *args, **kwargs) -> None:
        raise NotImplementedError
