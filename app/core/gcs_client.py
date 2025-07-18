from google.cloud import storage
from app.core.app_config import settings, logger


class GCSClient:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GCSClient, cls).__new__(cls)
            try:
                logger.info(f"Initializing GCS client: {settings.GCP_PROJECT}")
                cls._client = storage.Client()
                logger.info("Successfully initialized GCS client.")
            except Exception as e:
                logger.critical(
                    f"Failed to initialize GCS client at startup: {e}", exc_info=True
                )
                cls._client = None
        return cls._instance

    @property
    def client(self):
        if self._client is None:
            logger.error("Attempted to access uninitialized GCS client.")
            # This could happen if initialisation failed but the app continued.
            # You might want to re-attempt initialization or raise a specific error here.
            raise RuntimeError("Google Cloud Storage client is not initialized.")
        return self._client

    @property
    def bucket_name(self):
        return settings.GCS_BUCKET_NAME


# Initialize the GCS client globally when this module is imported
gcs_service = GCSClient()
