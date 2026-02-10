"""
Adapters Package

Bridges between new OODA Pydantic types and existing cognitive core.
"""

from .system_bridge import CognitiveBridge

__all__ = ["CognitiveBridge"]
