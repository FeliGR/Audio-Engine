from config import Config
from core.interfaces.logger_interface import ILogger
from utils.logger import LoggerFactory


class LoggerAdapter(ILogger):
    def __init__(self, name: str = "tts-service", config: object = None) -> None:
        if config is None:
            config = Config
        self._logger = LoggerFactory.get_logger(
            name=name,
            log_level=getattr(config, "LOG_LEVEL", "INFO"),
            log_to_file=getattr(config, "LOG_TO_FILE", False),
            log_file_path=getattr(config, "LOG_FILE_PATH", None),
        )

    def debug(self, message: str, *args, **kwargs) -> None:
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        self._logger.info(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        self._logger.error(message, *args, **kwargs)


app_logger = LoggerAdapter()
