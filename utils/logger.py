import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Optional, Union

from config import Config


class LoggerFactory:
    _loggers: Dict[str, logging.Logger] = {}

    @classmethod
    def get_logger(
        cls,
        name: str = "tts-service",
        log_level: Union[str, int] = "INFO",
        log_to_file: bool = False,
        log_file_path: Optional[str] = None,
        log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        max_bytes: int = 10485760,
        backup_count: int = 5,
    ) -> logging.Logger:
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)
        logger.handlers.clear()

        try:
            if isinstance(log_level, str):
                logger.setLevel(getattr(logging, log_level.upper()))
            else:
                logger.setLevel(log_level)
        except (AttributeError, TypeError) as e:

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.WARNING)
            logger.addHandler(console_handler)
            logger.warning(
                "Invalid log level: %s. Using INFO instead. Error: %s", log_level, e
            )
            logger.setLevel(logging.INFO)

        formatter = logging.Formatter(log_format)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_to_file:
            try:
                if not log_file_path:
                    log_dir = Path("logs")
                    log_dir.mkdir(exist_ok=True)
                    log_file_path = str(log_dir / f"{name}.log")

                file_handler = logging.handlers.RotatingFileHandler(
                    log_file_path, maxBytes=max_bytes, backupCount=backup_count
                )
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except (OSError, PermissionError, FileNotFoundError) as e:
                logger.warning("Failed to set up file logging: %s", e)

        cls._loggers[name] = logger
        return logger


def setup_logger(config=None):
    if config is None:
        config = Config

    return LoggerFactory.get_logger(
        name="tts-service",
        log_level=getattr(config, "LOG_LEVEL", "INFO"),
        log_to_file=getattr(config, "LOG_TO_FILE", False),
        log_file_path=getattr(config, "LOG_FILE_PATH", None),
    )
