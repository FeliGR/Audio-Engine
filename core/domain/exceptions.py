class TTSException(Exception):
    def __init__(self, message: str = "TTS operation failed") -> None:
        self.message = message
        super().__init__(self.message)


class TTSProcessingError(TTSException):
    def __init__(self, message: str = "TTS processing failed") -> None:
        super().__init__(message)


class TTSValidationError(TTSException):
    def __init__(self, message: str = "TTS request validation failed") -> None:
        super().__init__(message)


class TTSConfigurationError(TTSException):
    def __init__(self, message: str = "TTS configuration error") -> None:
        super().__init__(message)


class STTException(Exception):
    def __init__(self, message: str = "STT operation failed") -> None:
        self.message = message
        super().__init__(self.message)


class STTProcessingError(STTException):
    def __init__(self, message: str = "STT processing failed") -> None:
        super().__init__(message)


class STTValidationError(STTException):
    def __init__(self, message: str = "STT request validation failed") -> None:
        super().__init__(message)


class STTConfigurationError(STTException):
    def __init__(self, message: str = "STT configuration error") -> None:
        super().__init__(message)
