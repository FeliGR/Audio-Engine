from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")


class UseCaseInterface(ABC):
    @abstractmethod
    def execute(self, request: T) -> R:
        raise NotImplementedError
