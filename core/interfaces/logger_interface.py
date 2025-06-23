"""
Logger Interface Module

This module defines the ILogger interface, providing an abstract base for
logging implementations. Classes implementing this interface must provide methods
for debug, info, and error level logging.
"""

from abc import ABC, abstractmethod


class ILogger(ABC):
    """
    Interface for logging implementations.

    Classes implementing this interface must provide methods for
    debug, info, and error level logging.
    """

    @abstractmethod
    def debug(self, message: str, *args, **kwargs) -> None:
        """
        Log a debug-level message.

        Args:
            message (str): The debug message to be logged.
            *args: Additional positional arguments for message formatting.
            **kwargs: Additional keyword arguments.
        """

    @abstractmethod
    def info(self, message: str, *args, **kwargs) -> None:
        """
        Log an info-level message.

        Args:
            message (str): The info message to be logged.
            *args: Additional positional arguments for message formatting.
            **kwargs: Additional keyword arguments.
        """

    @abstractmethod
    def error(self, message: str, *args, **kwargs) -> None:
        """
        Log an error-level message.

        Args:
            message (str): The error message to be logged.
            *args: Additional positional arguments for message formatting.
            **kwargs: Additional keyword arguments.
        """
