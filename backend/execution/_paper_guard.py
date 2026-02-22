"""
Centrale paper mode guard — importeer dit in ALLE execution modules.
Eén enkel punt van waarheid voor de veiligheidswet.

Dit is de KRITIEKE VEILIGHEIDSLAAG die voorkomt dat er per ongeluk
live orders naar exchanges worden gestuurd tijdens paper trading.
"""

import os
import logging
from functools import wraps
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger("PaperGuard")

TRADING_MODE = os.getenv("TRADING_MODE", "paper")


class PaperModeViolation(Exception):
    """
    Raised when paper mode is violated.
    
    Dit wordt ge-raise wanneer code probeert een echte exchange call te doen
    terwijl TRADING_MODE=paper is geconfigureerd.
    """
    pass


class PaperGuardAuditLogger:
    """Centrale audit logger voor paper guard intercepties."""
    
    def __init__(self):
        self.logger = logging.getLogger("PaperGuardAudit")
    
    async def log_intercept(self, func_name: str, args: tuple, kwargs: dict, session_id: str = None):
        """
        Log een geïntercepteerde exchange call naar de audit trail.
        
        Args:
            func_name: Naam van de geblokkeerde functie
            args: Positional arguments
            kwargs: Keyword arguments
            session_id: ID van de actieve paper trading sessie
        """
        audit_entry = {
            "event": "paper_guard_intercept",
            "function": func_name,
            "trading_mode": "paper",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "intercepted": True,
            "session_id": session_id,
            "intent": self._extract_intent(args, kwargs),
        }
        
        # Structured logging naar console/file
        self.logger.warning(f"[PAPER_GUARD_INTERCEPT] {audit_entry}")
        
        # Schrijf ook naar sessiebestand als er een actieve sessie is
        await self._write_to_session_file(audit_entry)
        
        return audit_entry
    
    def _extract_intent(self, args: tuple, kwargs: dict) -> dict:
        """Extract trading intentie uit de arguments."""
        intent = {}
        
        # Probeer symbol, side, qty, price te extracten
        all_args = list(args) + list(kwargs.values())
        
        for arg in all_args:
            if isinstance(arg, str):
                if "/" in arg and not intent.get("symbol"):
                    intent["symbol"] = arg
                elif arg.upper() in ["BUY", "SELL"]:
                    intent["side"] = arg
            elif isinstance(arg, (int, float)):
                if arg > 100 and not intent.get("price"):
                    intent["price"] = arg
                elif 0 < arg < 100 and not intent.get("qty"):
                    intent["qty"] = arg
        
        return intent
    
    async def _write_to_session_file(self, audit_entry: dict):
        """Schrijf audit entry naar het actieve sessiebestand."""
        import json
        import glob
        
        # Zoek het meest recente sessiebestand
        session_files = glob.glob("real_paper_session_*.json")
        if not session_files:
            return
        
        latest = max(session_files, key=os.path.getmtime)
        
        try:
            with open(latest, "r+") as f:
                data = json.load(f)
                
                # Voeg audit_intercepts toe als nog niet bestaat
                if "audit_intercepts" not in data:
                    data["audit_intercepts"] = []
                
                data["audit_intercepts"].append(audit_entry)
                
                f.seek(0)
                json.dump(data, f, indent=2, default=str)
                f.truncate()
        except Exception as e:
            logger.error(f"Failed to write audit to session file: {e}")


# Globale audit logger instance
_audit_logger = PaperGuardAuditLogger()


def paper_guard(func: Callable) -> Callable:
    """
    Decorator die ALLE exchange order calls intercepteert.
    
    Gebruik op elke methode die een order naar een exchange stuurt.
    
    Voorbeeld:
        @paper_guard
        async def create_order(self, symbol: str, side: str, qty: float):
            # Deze code wordt NOOIT bereikt in paper mode
            return await self.exchange.create_order(...)
    
    Raises:
        PaperModeViolation: Als TRADING_MODE=paper
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        if TRADING_MODE == "paper":
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            logger.warning(
                f"[PAPER_GUARD] INTERCEPTED: {func_name} "
                f"ARGS={args[1:]} KWARGS={kwargs} — "
                f"ORDER NOT SENT TO EXCHANGE @ {datetime.now(timezone.utc).isoformat()}"
            )
            
            # Schrijf naar audit log
            try:
                await _audit_logger.log_intercept(func_name, args, kwargs)
            except Exception as e:
                logger.error(f"Audit logging failed: {e}")
            
            # Update Prometheus metric als beschikbaar
            try:
                from backend.monitoring.paper_metrics import PAPER_GUARD_INTERCEPTS
                PAPER_GUARD_INTERCEPTS.labels(function=func_name).inc()
            except ImportError:
                pass
            except Exception:
                # Metric update faalt niet kritiek
                pass
            
            raise PaperModeViolation(
                f"Blocked: {func_name} attempted real exchange call in paper mode. "
                f"Trading mode is set to 'paper'. No real order was sent."
            )
        
        return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        if TRADING_MODE == "paper":
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            logger.warning(
                f"[PAPER_GUARD] INTERCEPTED (sync): {func_name} "
                f"ARGS={args[1:]} KWARGS={kwargs}"
            )
            
            raise PaperModeViolation(
                f"Blocked: {func_name} attempted real exchange call in paper mode"
            )
        
        return func(*args, **kwargs)
    
    # Return juiste wrapper op basis van async of sync
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def get_audit_logger() -> PaperGuardAuditLogger:
    """Geef de globale audit logger instance terug."""
    return _audit_logger


def verify_paper_mode() -> bool:
    """
    Verifieer dat we in paper mode draaien.
    
    Returns:
        True als TRADING_MODE=paper
        
    Raises:
        PaperModeViolation: Als TRADING_MODE != "paper"
    """
    if TRADING_MODE != "paper":
        raise PaperModeViolation(
            f"CRITICAL: TRADING_MODE='{TRADING_MODE}' is not 'paper'. "
            f"Set TRADING_MODE=paper in environment before starting."
        )
    return True


# Import asyncio hier onderaan om circular imports te voorkomen
import asyncio
