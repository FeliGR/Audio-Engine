"""
Logger Module

This module provides logging functionality for the TTS Service application.
It offers a centralized logging setup with both console and file output options,
along with configuration for log levels, rotation, and formatting.

The module uses a factory pattern to create and cache logger instances, ensuring
consistent logging behavior throughout the application.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Optional, Union

from config import Config


class LoggerFactory:
    """
    Factory class for creating and managing logger instances.

    This class implements the factory pattern to create, configure, and cache
    logger instances. It ensures that loggers with the same name return the same
    instance and provides options for console and file logging with various
    configuration settings.

    Attributes:
        _loggers (Dict[str, logging.Logger]): Cache of created logger instances.
    """

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
        """
        Get or create a logger with specified configuration.

        Args:
            name (str): The name of the logger. Defaults to "tts-service".
            log_level (Union[str, int]): The logging level. Defaults to "INFO".
            log_to_file (bool): Whether to log to a file. Defaults to False.
            log_file_path (Optional[str]): Path to the log file. If None, a default path is used.
            log_format (str): The format string for log messages.
            max_bytes (int): Maximum size in bytes for log file before rotation. Defaults to 10MB.
            backup_count (int): Number of backup log files to keep. Defaults to 5.

        Returns:
            logging.Logger: Configured logger instance.
        """
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
            # Use a fallback handler to log the error
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
    """
    Set up and configure the application logger.

    This function creates a logger for the application using configuration
    parameters from the provided config object or the default Config.

    Args:
        config (object, optional): Configuration object with logging settings.
            If None, the default Config is used.

    Returns:
        logging.Logger: Configured application logger.
    """
    if config is None:
        config = Config

    return LoggerFactory.get_logger(
        name="tts-service",
        log_level=getattr(config, "LOG_LEVEL", "INFO"),
        log_to_file=getattr(config, "LOG_TO_FILE", False),
        log_file_path=getattr(config, "LOG_FILE_PATH", None),
    )
