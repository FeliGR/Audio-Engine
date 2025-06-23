"""
TTS Domain Exceptions Module

This module defines custom exceptions for the TTS service domain layer.
These exceptions provide specific error handling for different TTS scenarios.
"""


class TTSException(Exception):
    """Base exception class for TTS-related errors."""

    def __init__(self, message: str = "TTS operation failed") -> None:
        """
        Initialize the TTS exception.

        Args:
            message: Error message describing the exception.
        """
        self.message = message
        super().__init__(self.message)


class TTSProcessingError(TTSException):
    """Exception raised when TTS processing fails."""

    def __init__(self, message: str = "TTS processing failed") -> None:
        """
        Initialize the TTS processing error.

        Args:
            message: Error message describing the processing failure.
        """
        super().__init__(message)


class TTSValidationError(TTSException):
    """Exception raised when TTS request validation fails."""

    def __init__(self, message: str = "TTS request validation failed") -> None:
        """
        Initialize the TTS validation error.

        Args:
            message: Error message describing the validation failure.
        """
        super().__init__(message)


class TTSConfigurationError(TTSException):
    """Exception raised when TTS configuration is invalid."""

    def __init__(self, message: str = "TTS configuration error") -> None:
        """
        Initialize the TTS configuration error.

        Args:
            message: Error message describing the configuration issue.
        """
        super().__init__(message)
