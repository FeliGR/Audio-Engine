"""
Configuration Module

This module contains configuration classes for the TTS Engine application.
It provides a base configuration as well as settings for development, production,
and testing environments.
"""

import os


class Config:
    """
    Base configuration class.

    Attributes:
        DEBUG (bool): Enables or disables debug mode.
        TESTING (bool): Indicates if the application is in testing mode.
        LOG_LEVEL (str): Defines the logging level.
        API_RATE_LIMIT (int): The API rate limit setting.
        SECRET_KEY (str): Secret key used for application security.
        VERSION (str): Application version.
        HOST (str): Host address for binding.
        PORT (int): Port number for binding.
        CORS_ORIGINS (str): Allowed origins for Cross-Origin Resource Sharing.
    """

    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
    TESTING = os.environ.get("TESTING", "False").lower() == "true"
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    API_RATE_LIMIT = int(os.environ.get("API_RATE_LIMIT", "100"))
    SECRET_KEY = os.environ.get("SECRET_KEY", "development-key-change-in-production")

    VERSION = "0.1.0"
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 5003))
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    DEFAULT_RATE_LIMITS = ["100 per day", "10 per minute"]


class DevelopmentConfig(Config):
    """
    Development configuration class.

    Inherits from Config and sets configuration settings specific to the development environment.
    """

    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """
    Production configuration class.

    Inherits from Config and sets configuration settings specific to the production environment.
    """

    DEBUG = False
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING")


class TestingConfig(Config):
    """
    Testing configuration class.

    Inherits from Config and sets configuration settings specific to the testing environment.
    """

    TESTING = True
    DEBUG = True
    LOG_LEVEL = "DEBUG"
