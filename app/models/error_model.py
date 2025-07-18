from pydantic import BaseModel
from typing import Optional, Dict, Any

class ErrorResponse(BaseModel):
    code: str  # A unique error code (e.g., "FILE_NOT_FOUND", "GCS_PERMISSION_DENIED")
    message: str # A human-readable message for the developer/operator
    details: Optional[Dict[str, Any]] = None # Optional: more granular, technical details

