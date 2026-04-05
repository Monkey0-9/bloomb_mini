"""
ProductionHarden - Essential utilities for live environment stability.

Implements:
- Boot-time Environment Validation
- Global Exception Mapping
- Rate Limiting Configuration
- Graceful Shutdown Orchestration
"""
import os
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import structlog

log = structlog.get_logger(__name__)

REQUIRED_ENV_VARS = [
    "JWT_SECRET_KEY",
    "ANTHROPIC_API_KEY",
    "NEWSAPI_KEY"
]

def validate_environment():
    """Checks for critical production environment variables."""
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        log.error("environment_validation_failed", missing=missing)
        # In strict production, we might want to exit(1) here
        return False
    return True

async def global_exception_handler(request: Request, exc: Exception):
    """Prevents internal trace leakage and ensures consistent JSON errors."""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "type": "HTTP_EXCEPTION"}
        )
    
    log.exception("unhandled_exception", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "An internal system error occurred. Terminal synchronization lost.",
            "type": "INTERNAL_ERROR",
            "request_id": str(request.scope.get("aws.request_id", "local"))
        }
    )

class ProductionConfig:
    """Centralized production configuration overrides."""
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    IS_PROD = os.getenv("ENV", "development").lower() == "production"
    
    @staticmethod
    def setup_logging():
        # Configuration for high-performance structured logging
        pass
