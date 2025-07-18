import logging
import os
import sys
import json
from datetime import datetime
from contextvars import ContextVar

# ContextVars for trace and span IDs
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[str | None] = ContextVar("span_id", default=None)

class StructuredLogFormatter(logging.Formatter):
    """
    A custom logging formatter that outputs logs in Google Cloud's structured logging format (JSON),
    including trace_id and span_id from ContextVars, and mapping log levels to severity.
    """
    def __init__(self, project_id: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_id = project_id

    def format(self, record: logging.LogRecord) -> str:
        # Ensure record.message is set, as the base Formatter.format usually does this
        # before calling formatMessage if it were not overridden.
        record.message = record.getMessage()

        # Get trace and span IDs from ContextVars
        trace_id = trace_id_var.get()
        span_id = span_id_var.get()

        # Map standard logging levels to Google Cloud Logging severity levels
        severity_map = {
            'CRITICAL': 'CRITICAL',
            'ERROR': 'ERROR',
            'WARNING': 'WARNING',
            'INFO': 'INFO',
            'DEBUG': 'DEBUG',
            'NOTSET': 'DEFAULT'
        }
        severity = severity_map.get(record.levelname, 'DEFAULT')

        # Build the base log entry as a dictionary
        log_entry = {
            "severity": severity,
            "message": record.message, # Use the explicitly set record.message
            "timestamp": datetime.fromtimestamp(record.created).isoformat(timespec='milliseconds') + "Z", # ISO 8601 with milliseconds and Z for UTC
            "logging.googleapis.com/sourceLocation": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            },
            "logging.googleapis.com/labels": {
                "python_logger": record.name,
            }
        }

        # Add trace and span info if available and project_id is set
        if trace_id and self.project_id:
            # Google Cloud Trace format: projects/<PROJECT_ID>/traces/<TRACE_ID>
            log_entry["logging.googleapis.com/trace"] = f"projects/{self.project_id}/traces/{trace_id}"
        if span_id:
            log_entry["logging.googleapis.com/spanId"] = span_id
        # Optional: Add trace_sampled if you implement sampling logic
        # log_entry["logging.googleapis.com/trace_sampled"] = True

        # If there's an exception, add it to the log entry
        if record.exc_info:
            # formatException returns a string with traceback
            log_entry["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            # formatStack returns a string with stack information
            log_entry["stack_trace"] = self.formatStack(record.stack_info)

        # Serialize the dictionary to a JSON string
        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO", project_id: str | None = None):
    """
    Configures basic stream (console) logging for the application,
    integrating Google Structured Logging with Trace ID and Span ID.

    Reads the desired log level from the environment variable `LOG_LEVEL`,
    defaulting to the `log_level` argument if the environment variable is not set
    or invalid.

    Args:
        log_level: The default log level string (e.g., "INFO", "DEBUG") if
                   `LOG_LEVEL` environment variable is not set.
        project_id: The Google Cloud Project ID, required for trace correlation.
    """
    # Prioritize environment variable for log level
    effective_log_level_str = os.getenv("LOG_LEVEL", log_level).upper()
    log_level_int = getattr(logging, effective_log_level_str, None)

    # Validate the resolved log level
    if not isinstance(log_level_int, int):
        print(
            f"Warning: Invalid LOG_LEVEL '{effective_log_level_str}'. Defaulting to INFO."
        )
        log_level_int = logging.INFO
        effective_log_level_str = "INFO"

    # Use our custom StructuredLogFormatter
    formatter = StructuredLogFormatter(project_id=project_id)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level_int)

    # Clear existing handlers to prevent duplicate logs
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add console handler (StreamHandler)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter) # Set our custom formatter
    logger.addHandler(console_handler)
    print(
        f"Console logging handler added with root level {effective_log_level_str}"
    )

    # --- Optional: Adjust log levels for specific noisy libraries ---
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Get a logger for this module and log completion message
    module_logger = logging.getLogger(__name__)
    module_logger.info(
        f"Logging setup complete. Root level set to {effective_log_level_str}."
    )

def get_logger() -> logging.Logger:
    """
    Returns the configured root logger.
    """
    return logging.getLogger()
