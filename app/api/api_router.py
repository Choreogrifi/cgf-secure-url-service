from fastapi import APIRouter
from app.core.app_config import logger

api_router = APIRouter()

try:
    from app.api.endpoints import gcs_url_endpoint

    api_router.include_router(
        gcs_url_endpoint.router, prefix="/url", tags=["Google Cloud Storage"]
    )
    logger.info("Google Cloud Storage endpoint router successfully included at /")
except ImportError as e:
    logger.warning(
        "Google Cloud Storage endpoint router could not be imported. This route will be skipped.",
        exc_info=True,  # includes stack trace
    )
except Exception as e:
    logger.error(
        f"Unexpected error when including Google Cloud Storage endpoint router : {e}",
        exc_info=True,
    )
