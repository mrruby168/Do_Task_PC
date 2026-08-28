"""
PC Tool Server - API Module

API routes initialization.
"""

from app.api.tools import router as tools_router
from app.api.tasks import router as tasks_router
from app.api.approvals import router as approvals_router
from app.api.system import router as system_router
from app.api.health import router as health_router

__all__ = [
    "tools_router",
    "tasks_router", 
    "approvals_router",
    "system_router",
    "health_router",
]
