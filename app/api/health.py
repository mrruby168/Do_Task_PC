"""
PC Tool Server - Health Check API

Health check and status endpoints.
"""

from fastapi import APIRouter, Depends
from typing import Any, Dict

from app.config import get_config


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check() -> Dict[str, Any]:
    """Check server health."""
    config = get_config()
    
    return {
        "status": "healthy",
        "app_name": config.APP_NAME,
        "version": config.APP_VERSION,
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, bool]:
    """Check if server is ready."""
    return {"ready": True}
