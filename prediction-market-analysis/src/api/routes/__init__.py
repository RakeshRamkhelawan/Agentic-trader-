"""API Routes."""

from src.api.routes.analysis import router as analysis_router
from src.api.routes.health import router as health_router
from src.api.routes.signals import router as signals_router

__all__ = ["health_router", "signals_router", "analysis_router"]
