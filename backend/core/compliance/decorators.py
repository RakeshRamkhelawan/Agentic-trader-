import functools
import inspect
import logging
from typing import Any, Optional

from backend.core.auth.context import (get_current_tenant_optional,
                                       get_current_user_optional)

logger = logging.getLogger(__name__)

# Global reference to be set by main application
_audit_logger = None


def set_global_audit_logger(audit_logger):
    global _audit_logger
    _audit_logger = audit_logger


def audit_decision(action: str, resource_type: str):
    """
    Decorator to audit log a function call.
    Automatically captures args, result, tenant_id, and user_id.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the function first
            try:
                result = await func(*args, **kwargs)
                status = "SUCCESS"
                details = {
                    "args": str(args),
                    "kwargs": str(kwargs),
                    "result": str(result),
                }
            except Exception as e:
                status = "FAILURE"
                details = {"args": str(args), "kwargs": str(kwargs), "error": str(e)}
                raise e
            finally:
                # Log to audit trail
                if _audit_logger:
                    try:
                        tenant_id = get_current_tenant_optional() or "unknown"
                        user_id = get_current_user_optional() or "system"

                        # Try to extract resource_id from result if dict
                        resource_id = "unknown"
                        if isinstance(result, dict):
                            resource_id = str(
                                result.get("id") or result.get("order_id") or "unknown"
                            )

                        await _audit_logger.log_event(
                            tenant_id=tenant_id,
                            action=action,
                            resource_type=resource_type,
                            resource_id=resource_id,
                            actor_id=user_id,
                            details=details,
                            status=status,
                        )
                    except Exception as log_err:
                        logger.error(f"Failed to audit log {action}: {log_err}")

            return result

        return wrapper

    return decorator
