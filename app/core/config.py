import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from dotenv import load_dotenv


# This class defines all possible settings and their default values.
# Environment-specific settings will inherit from this and override defaults.
class BaseAppSettings(BaseSettings):
    """
    Base application settings.
    Values are loaded from environment variables (case-insensitive by default in v2).
    """

    # Logging Level (can be controlled by environment variable)
    LOG_LEVEL: str = "INFO"

    # Pydantic V2 uses model_config instead of inner Config class
    model_config = SettingsConfigDict(
        case_sensitive=False,  # Environment variables are typically case-insensitive
        extra="ignore",  # Ignore extra fields from environment variables
    )
    PROJECT_NAME: str = "Abacus Signed URL Generator"
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"

    API_V1_STR: str = "/v1"
    DEBUG: bool = False  # Add a general debug flag
    GCS_BUCKET_NAME: str = "abacus-claims"


class BootstrapSettings(BaseAppSettings):
    GCP_PROJECT: str = None


class LocalSettings(BaseAppSettings):
    ENVIRONMENT: str = "local"
    GCP_PROJECT: str = "grpit-cds-sandpit-dev"
    LOG_LEVEL: str = "DEBUG"  # Most verbose for local debugging
    DEBUG: bool = True
    GCS_BUCKET_NAME: str = "abacus-claims"


class DevelopmentSettings(BaseAppSettings):
    ENVIRONMENT: str = "development"
    GCP_PROJECT: str = ""  # Replace with your actual project ID
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    GCS_BUCKET_NAME: str = "abacus-claims-dev"


class TestSettings(BaseAppSettings):
    ENVIRONMENT: str = "test"
    GCP_PROJECT: str = ""  # Replace with your actual project ID
    LOG_LEVEL: str = "WARNING"
    DEBUG: bool = False
    GCS_BUCKET_NAME: str = ""


class StagingSettings(BaseAppSettings):
    ENVIRONMENT: str = "staging"
    GCP_PROJECT: str = ""
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    GCS_BUCKET_NAME: str = ""


class ProductionSettings(BaseAppSettings):
    ENVIRONMENT: str = "production"
    GCP_PROJECT: str = ""
    LOG_LEVEL: str = "WARNING"
    DEBUG: bool = False
    GCS_BUCKET_NAME: str = ""


# This dictionary maps environment names to their corresponding Settings classes.
_environment_settings_map = {
    "local": LocalSettings,
    "development": DevelopmentSettings,
    "test": TestSettings,
    "staging": StagingSettings,
    "production": ProductionSettings,
}


def get_bootstrap_settings() -> BootstrapSettings:
    load_dotenv()
    env_file_path = f".env.{os.environ.get('ENVIRONMENT', 'local').lower()}"

    if os.path.exists(env_file_path):
        load_dotenv(dotenv_path=env_file_path, override=True)

    return BootstrapSettings()


_settings_instance: Optional[BaseAppSettings] = None


def get_setings() -> BaseAppSettings:
    global _settings_instance
    if _settings_instance:
        return _settings_instance

    load_dotenv()
    env_file_path = f".env.{os.environ.get('ENVIRONMENT', 'local').lower()}"

    if os.path.exists(env_file_path):
        load_dotenv(dotenv_path=env_file_path, override=True)

    current_environment_name = os.environ.get("ENVIRONMENT", "local").lower()

    # Get the appropriate Settings class based on the environment name.
    settings_class = _environment_settings_map.get(current_environment_name)

    # Handle unknown environments gracefully by falling back to 'local'
    if not settings_class:
        settings_class = LocalSettings

    # Instantiate settings
    # Pydantic-settings will now load values based on the chosen SettingsClass hierarchy
    # and environment variables will override any defaults defined in the classes.
    try:
        settings_class.GCP_PROJECT = os.environ.get("GCP_PROJECT")
        _settings_instance = settings_class()
        return _settings_instance
    except Exception as e:
        import sys

        sys.exit("Failed to load critical application settings.")
