"""
API Routes
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .records import router as records_router
from .stats import router as stats_router
from .tables import router as tables_router
from .reports import router as reports_router
from .settings import router as settings_router

api_router = APIRouter()

# Public routes (no authentication required)
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])

# Protected routes (authentication required)
api_router.include_router(records_router, prefix="/records", tags=["records"])
api_router.include_router(stats_router, prefix="/stats", tags=["stats"])
api_router.include_router(tables_router, prefix="/tables", tags=["tables"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])