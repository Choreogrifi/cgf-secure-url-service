import time
import uuid
import os
import binascii

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

# Import both ContextVars and logger from the logging_config module
from app.utils.logging_config import trace_id_var, span_id_var, get_logger
# Get the configured logger
logger = get_logger()
class TraceMiddleware(BaseHTTPMiddleware):
    """
    Middleware that performs the following for each HTTP request:
    1. Generates a unique Trace ID (UUID).
    2. Stores the Trace ID in `request.state.trace_id` for access within the request lifecycle.
    3. Sets the Trace ID in a `ContextVar` so it's available to the logging system.
    4. Logs the start of the request with the Trace ID.
    5. Processes the request by calling the next middleware/endpoint (`call_next`).
    6. Adds `X-Trace-ID` and `X-Process-Time` headers to the outgoing response.
    7. Logs the end of the request with the Trace ID, status code, and processing time.
    8. Resets the `ContextVar` to prevent ID leakage between requests.
    """
    def __init__(self, app: ASGIApp):
        """
        Initializes the TraceMiddleware.

        Args:
            app: The ASGI application that this middleware wraps (the next callable
                 in the middleware chain or the FastAPI application itself).
        """
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Main middleware processing logic.

        Args:
            request: The incoming FastAPI/Starlette Request object.
            call_next: A function to call to pass the request to the next middleware or endpoint.

        Returns:
            The FastAPI/Starlette Response object.
        """
        # 1. Generate unique trace ID
        trace_id = str(uuid.uuid4())
        span_id = binascii.hexlify(os.urandom(8)).decode('ascii')

        # 2. Store trace_id in request state (for direct access in routes if needed)
        request.state.trace_id = trace_id
        request.state.span_id = span_id

        # 3. Set the trace ID in the ContextVar.
        # This token is used to reset the ContextVar after the request is processed.
        trace_token = trace_id_var.set(trace_id)
        span_token = span_id_var.set(span_id) 

        # Log request start (this log will now automatically include the trace_id)
        start_time = time.perf_counter()
        logger.info(f"Request started: {request.method} {request.url.path}")

        response: Response = Response(status_code=500)
        try:
            logger.info(
                f"URL to be processed: {request.url.path} and base path: {request.base_url}"
            )
            response = await call_next(request)
            # Response object is now available after the request has been processed by endpoint/other middleware
        except Exception as e:
            # Catch exceptions raised further down the chain (endpoints, other middleware)
            process_time = time.perf_counter() - start_time
            logger.error(
                f"Exception during request processing: {e} "
                f"({process_time:.4f}s)",
                exc_info=True,  # Log traceback
            )
            # Re-raise the caught exception to allow FastAPI's exception handlers to process it
            raise e
        finally:
            pass
            
        process_time = time.perf_counter() - start_time

        # Add custom headers to the *successful* response
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Span-ID"] = span_id
                        
        logger.info(f"Request finished: Status {response.status_code} ({process_time:.4f}s)")
        
        trace_id_var.reset(trace_token)
        span_id_var.reset(span_token)

        return response