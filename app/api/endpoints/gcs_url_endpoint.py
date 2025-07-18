from fastapi import APIRouter, HTTPException, Query, status
from datetime import timedelta
from app.core.app_config import settings, logger
from app.core.gcs_client import gcs_service
from google.auth import default
from google.auth.transport.requests import Request  # Make sure this is imported
from google.auth.exceptions import DefaultCredentialsError  # Make sure this is imported
from google.auth.compute_engine.credentials import (
    Credentials as ComputeEngineCredentials,
)  # For type checking

router = APIRouter()


@router.get("/", response_description="Signed URL generated successfully")
def generate_signed_url(
    filename: str = Query(
        ..., description="Filename in GCS (e.g., 'path/to/my_file.txt')"
    ),
    expires_in: int = Query(
        300, ge=20, le=3600, description="Expiration time in seconds (min 60, max 3600)"
    ),
):
    """
    **Generate a signed URL** to securely download a Google Cloud Storage object.

    This endpoint creates a time-limited URL that grants temporary access to a
    specific file in the configured GCS bucket, allowing downloads without
    requiring Google Cloud authentication.
    """
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    logger.info(
        f"Received request to generate signed URL for filename: '{filename}' (expiry: {expires_in}s)."
    )

    try:
        credentials, settings.GCP_PROJECT = default(
            scopes=scopes
        )  # Correctly imported 'default'

        logger.info(f"Credentials object type: {type(credentials)}")
        # Use getattr safely in case service_account_email is genuinely not present (though it should be for ComputeEngineCredentials)
        sa_email_from_credentials = getattr(
            credentials, "service_account_email", "UNKNOWN_SERVICE_ACCOUNT_EMAIL"
        )
        logger.info(
            f"Credentials service_account_email (from object): {sa_email_from_credentials}"
        )
        logger.info(
            f"Credentials token: {'exists' if credentials.token else 'does not exist'}"
        )
        logger.info(f"Project ID from default(): {settings.GCP_PROJECT}")

        # Check if credentials are valid and refresh them
        if not credentials.valid:
            logger.error(
                "Invalid Google Cloud credentials detected. Attempting refresh."
            )
            # Ensure auth_request is defined outside the conditional if not always needed
            auth_request = Request()
            credentials.refresh(auth_request)
            if not credentials.valid:
                logger.error("Credentials remain invalid after refresh.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid Google Cloud credentials. Please check your Cloud Run service account configuration and permissions.",
                )

        # Get the service account email that will do the signing
        # This will be the attached Cloud Run service account
        signing_service_account_email = None
        if (
            isinstance(credentials, ComputeEngineCredentials)
            and credentials.service_account_email
        ):
            signing_service_account_email = credentials.service_account_email
        if not signing_service_account_email:
            logger.error(
                "Could not determine service account email for signing the URL."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not determine the service account identity for URL signing. Check Cloud Run service account configuration.",
            )

        bucket = gcs_service.client.bucket(gcs_service.bucket_name)
        blob = bucket.blob(filename)

        if not blob.exists():
            logger.warning(
                f"File not found in GCS for signed URL generation: '{filename}'."
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in Google Cloud Storage.",
            )

        # Pass service_account_email and access_token directly to blob.generate_signed_url
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expires_in),
            method="GET",
            service_account_email=signing_service_account_email,
            access_token=credentials.token,
            response_disposition=f"attachment; filename={filename}",
        )
        logger.info(f"Successfully generated signed URL for filename: '{filename}'.")
        return {"signed_url": url}

    except DefaultCredentialsError as e:
        logger.exception(f"Google Cloud authentication failed for '{filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication to Google Cloud failed. Please check your Cloud Run service account permissions.",
        )
    except Exception as e:
        logger.exception(
            f"An unexpected error occurred during signed URL generation for '{filename}': {e}"
        )
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error: Could not generate signed URL. Please check server logs.",
        )
