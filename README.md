# EngFileDownloader Service

## Introduction

EngFileDownloader is a FastAPI-based microservice that generates signed URLs for securely downloading files from Google Cloud Storage. It provides a
simple API endpoint that creates time-limited URLs, allowing temporary access to specific files without requiring Google Cloud authentication.

## Features

- Generate secure, time-limited signed URLs for file downloads
- Configurable expiration time for URLs
- Automatic file existence verification
- Comprehensive error handling
- Structured error responses
- Environment-specific configuration
- Cloud Run deployment support
- Logging and monitoring

## Architecture

- **API Endpoints**: RESTful API built with FastAPI that provides endpoints for generating signed URLs
- **Data Models**: Pydantic models for request/response validation and error handling
- **Configuration**: Environment-specific settings using Pydantic BaseSettings with support for .env files

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Google Cloud SDK
- Google Cloud Storage bucket
- Service account with appropriate permissions

### Environment Variables

| Variable        | Description                                                            |
|-----------------|------------------------------------------------------------------------|
| ENVIRONMENT     | Deployment environment (local, development, test, staging, production) |
| GCP_PROJECT     | Google Cloud Platform project ID                                       |
| LOG_LEVEL       | Logging level (INFO, DEBUG, WARNING, ERROR)                            |
| DEBUG           | Enable debug mode (True/False)                                         |
| GCS_BUCKET_NAME | Google Cloud Storage bucket name                                       |
| PORT            | Port for the FastAPI application (default: 8080)                       |

## Configuration

The application uses a hierarchical configuration system with environment-specific settings:

- **BaseAppSettings:** Base configuration with default values
- **LocalSettings:** Configuration for local development
- **DevelopmentSettings:** Configuration for development environment
- **TestSettings:** Configuration for test environment
- **StagingSettings:** Configuration for staging environment
- **ProductionSettings:** Configuration for production environment

Configuration is loaded from environment variables and .env files, with environment-specific .env files taking precedence.

## Application Structure

```
EngFileDownloader/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   └── gcs_url_endpoint.py  # URL generation endpoint
│   │   └── api_router.py            # API router configuration
│   ├── core/
│   │   ├── app_config.py            # Application configuration
│   │   ├── config.py                # Environment-specific settings
│   │   └── gcs_client.py            # Google Cloud Storage client
│   ├── middleware/
│   │   └── trace_middleware.py      # Tracing middleware
│   ├── models/
│   │   └── error_model.py           # Error response model
│   ├── utils/
│   │   └── logging_config.py        # Logging configuration
│   └── main.py                      # FastAPI application entry point
├── Dockerfile                       # Docker configuration
├── deploy.sh                        # Deployment script
├── requirements.txt                 # Python dependencies
└── README.md                        # Project documentation
```

### Key Components

- **FastAPI Application**: The main application entry point that configures routes, middleware, and exception handlers
- **API Router**: Configures and includes API endpoints
- **GCS URL Endpoint**: Generates signed URLs for file downloads
- **GCS Client**: Singleton class for interacting with Google Cloud Storage
- **Configuration**: Environment-specific settings and application configuration
- **Error Model**: Pydantic model for structured error responses
- **Trace Middleware**: Middleware for request tracing

### Flow of Execution

1. Client sends a request to the `/v1/url/` endpoint with a filename and optional expiration time
2. The application validates the request parameters
3. The application checks if the file exists in the configured GCS bucket
4. If the file exists, the application generates a signed URL with the specified expiration time
5. The application returns the signed URL to the client
6. The client can use the signed URL to download the file directly from Google Cloud Storage

## API Documentation

- **Swagger UI**: Available at `/v1/docs` when the application is running
- **ReDoc**: Available at `/v1/redoc` when the application is running

### Main Endpoints

- **Generate Signed URL: `/v1/url/`**
  - `GET /`: Generate a signed URL for downloading a file from Google Cloud Storage
    - Query Parameters:
      - `filename` (required): Path to the file in GCS (e.g., 'path/to/my_file.txt')
      - `expires_in` (optional): Expiration time in seconds (default: 300, min: 20, max: 3600)
    - Response:
      - `200 OK`: Returns a JSON object with the signed URL
      - `404 Not Found`: File not found in Google Cloud Storage
      - `500 Internal Server Error`: Server error (authentication failure, etc.)

## Data Models

### ErrorResponse

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "error_type": "ExceptionType",
    "message": "Detailed error message",
    "request_path": "/v1/url/"
  }
}
```

## Error Handling

The application provides comprehensive error handling with structured error responses:

- **HTTP Exceptions**: Handled by the http_exception_handler, which returns a structured JSON response
- **Generic Exceptions**: Handled by the generic_exception_handler, which returns a 500 error with details
- **Specific Error Cases**:
  - File not found: 404 Not Found
  - Authentication failure: 500 Internal Server Error
  - Invalid credentials: 500 Internal Server Error
  - Service account not found: 500 Internal Server Error

## Local Development

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.local.txt`
5. Create a `.env.local` file with the required environment variables
6. Run the application: `python -m app.main`
7. Access the API documentation at http://localhost:8080/v1/docs

## Deployment

The service can be deployed to any environment that supports container images.

Deploy to Google Cloud Run using the provided deployment script:

```bash
./deploy.sh
```

This script:

1. Builds a Docker image using Cloud Build
2. Deploys the image to Cloud Run
3. Configures the service with appropriate memory, concurrency, and scaling settings
4. Sets required environment variables
5. Outputs the service URL upon successful deployment

The service is deployed with internal and cloud load balancing ingress, requiring authentication for access.
