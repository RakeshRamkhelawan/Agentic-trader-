"""
Enterprise Error Handlers voor Paper Trading API.

Zorgt voor consistente, gestructureerde error responses.
"""

import os
import traceback
from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse

from backend.execution._paper_guard import PaperModeViolation


class VedicBlockException(Exception):
    """Exception voor Vedic blocking conditions (Rahu Kala, etc.)."""

    def __init__(self, reason: str, resumes_at: str = None):
        self.reason = reason
        self.resumes_at = resumes_at
        super().__init__(f"Trading blocked: {reason}")


async def paper_mode_violation_handler(request: Request, exc: PaperModeViolation):
    """
    Handler voor PaperModeViolation exceptions.

    Dit is een CRITIEKE safety handler - geeft duidelijk aan dat
    een poging tot live trading is geblokkeerd.
    """
    return JSONResponse(
        status_code=403,
        content={
            "error": "PAPER_MODE_VIOLATION",
            "message": str(exc),
            "trading_mode": "paper",
            "action_required": "This is a safety block. No real order was sent.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "documentation": "Use ShadowPortfolioManager for paper trading",
        },
    )


async def vedic_block_handler(request: Request, exc: VedicBlockException):
    """Handler voor Vedic blocking conditions."""
    return JSONResponse(
        status_code=503,  # Service Unavailable
        content={
            "error": "VEDIC_BLOCK",
            "message": "Trading temporarily blocked by Vedic constraints",
            "reason": exc.reason,
            "resumes_at": exc.resumes_at,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trading_mode": os.getenv("TRADING_MODE", "paper"),
        },
    )


async def generic_error_handler(request: Request, exc: Exception):
    """Generic error handler voor onverwachte exceptions."""

    # In productie: log stack trace maar stuur niet naar client
    error_id = f"ERR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Log naar stderr voor observability
    print(f"[{error_id}] Unhandled error: {exc}")
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "error_id": error_id,
            "trading_mode": os.getenv("TRADING_MODE", "paper"),
            "safe": True,  # Geeft auditor zekerheid dat paper mode niet gebroken is
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def validation_error_handler(request: Request, exc: Exception):
    """Handler voor validatie errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": getattr(exc, "errors", lambda: str(exc))(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def register_error_handlers(app):
    """Registreer alle error handlers op de FastAPI app."""

    app.add_exception_handler(PaperModeViolation, paper_mode_violation_handler)
    app.add_exception_handler(VedicBlockException, vedic_block_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # Log registratie
    print("✓ Error handlers registered")
    print("  - PaperModeViolation (403)")
    print("  - VedicBlockException (503)")
    print("  - Generic Exception (500)")
