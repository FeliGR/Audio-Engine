"""
Use Case Interfaces Module

This module defines the base interface for all use cases in the application.
"""

from abc import ABC, abstractmethod
from typing import TypeVar

# Generic type for use case input and output
T = TypeVar("T")
R = TypeVar("R")


class UseCaseInterface(ABC):  # pylint: disable=too-few-public-methods
    """
    Base interface for all use cases.

    Use cases represent application-specific business rules and
    coordinate the flow of data between external interfaces and entities.
    """

    @abstractmethod
    def execute(self, request: T) -> R:
        """
        Execute the use case.

        Args:
            request: The input data for the use case.

        Returns:
            The result of the use case execution.
        """
        raise NotImplementedError
