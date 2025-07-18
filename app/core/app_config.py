# app/core/app_config.py
from functools import lru_cache
from app.core.config import get_setings, get_bootstrap_settings
from app.utils.logging_config import get_logger, setup_logging
from app.core.config import BaseAppSettings, BootstrapSettings
import logging


class AppConfig:
    """
    Centralized configuration manager for the FastAPI application.
    Initializes settings and logging once.
    """

    _settings: BaseAppSettings | None = None
    _bootstrap_settings: BootstrapSettings | None = None
    _logger: logging.Logger | None = None

    @classmethod
    @lru_cache(maxsize=1)  # Ensures the bootstrap settings are loaded only once
    def get_bootstrap_settings_cached(cls) -> BootstrapSettings:
        return get_bootstrap_settings()

    @classmethod
    def get_configured_logger(cls) -> logging.Logger:
        if cls._logger is None:
            bootstrap_settings = cls.get_bootstrap_settings_cached()
            setup_logging(project_id=bootstrap_settings.GCP_PROJECT)
            cls._logger = get_logger()
        return cls._logger

    @classmethod
    @lru_cache(maxsize=1)  # Ensures the main settings are loaded only once
    def get_settings_cached(cls) -> BaseAppSettings:
        return get_setings()

    @classmethod
    def initialize_app_config(cls):
        """
        Call this method explicitly at application startup to ensure
        all core components (like logging) are initialized.
        """
        _ = cls.get_configured_logger()  # Forces logger initialization
        _ = cls.get_settings_cached()  # Forces main settings loading
        # You can add other global initializations here if needed


# Expose instances for easy access
settings = AppConfig.get_settings_cached()
logger = AppConfig.get_configured_logger()
