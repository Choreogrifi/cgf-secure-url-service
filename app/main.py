from fastapi import FastAPI, HTTPException, status
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from starlette.requests import Request
import os
from datetime import datetime
from app.core.app_config import settings, logger, AppConfig
AppConfig.initialize_app_config()

from app.middleware.trace_middleware import TraceMiddleware
from app.models.error_model import ErrorResponse
from app.api.api_router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager to handle application startup and shutdown events.
    Registered with the FastAPI app instance.
    """
    logger.info(
        f"Lifespan: Starting up {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode."
    )
    # Perform any startup tasks here
    logger.info("Lifespan: Startup complete.")

    # Log loaded settings (be careful not to log sensitive information)
    logger.info(
        f"Settings loaded for environment {settings.ENVIRONMENT}: "
        f"LOG_LEVEL={settings.LOG_LEVEL}, "
        f"DEBUG={settings.DEBUG}, "
        f"GCP_PROJECT={settings.GCP_PROJECT}"
    )
    yield  # The application runs while yielded

    # --- Shutdown Logic ---
    logger.info(
        f"Lifespan: Shutting down {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode."
    )
    # Perform any shutdown tasks here
    logger.info("Lifespan: Shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Abacus generate a signed URL for file downloads.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,  # Register the lifespan context manager
)

# Add middleware
app.add_middleware(TraceMiddleware)

# Health check endpoint
@app.get("/echo/", tags=["Root"], include_in_schema=True)
async def root():
    """Echoes back the provided message"""

    return {
        "Project Name": settings.PROJECT_NAME,
        "Environment": settings.ENVIRONMENT,
        "API Version": settings.API_V1_STR,
        "Bucket Name": settings.GCS_BUCKET_NAME,
        "Debug Mode": settings.DEBUG,
        "Timestamp": datetime.now(),
    }

# Register exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handles FastAPI's HTTPException to return structured JSON responses."""
    logger.error(
        f"HTTPException caught for path '{request.url.path}': Status {exc.status_code}, Detail: {exc.detail}",
        extra={"detail": exc.detail, "status_code": exc.status_code, "request_path": request.url.path}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {"code": "HTTP_ERROR", "message": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catches any unexpected exceptions and returns a generic 500 error."""
    logger.exception(f"Unhandled exception caught for path '{request.url.path}': {exc}",
                     extra={"error_type": type(exc).__name__, "request_path": request.url.path})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            code="UNEXPECTED_ERROR",
            message="An unexpected server error occurred. Please try again later.",
            details={"error_type": type(exc).__name__, "message": str(exc), "request_path": request.url.path}
        ).model_dump()
    )

# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR, tags=["Google Cloud Storage"])

if __name__ == "__main__":
    import uvicorn

    # Logging and DB configuration should have already happened above
    logger.info(
        f"Starting Uvicorn server directly for local development on "
        f"http://127.0.0.1:{os.getenv('PORT', 8000)}"
    )
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )