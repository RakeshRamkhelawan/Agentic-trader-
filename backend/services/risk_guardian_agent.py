import logging
from typing import Any

# Basic Pydantic models for validation
from pydantic import ValidationError

from backend.core.memory_agent import MemoryAgent
from backend.schemas.agent_messages import AgentMessage
from backend.schemas.risk import AutonomyStatus, RiskProfile


class RiskGuardianAgent:
    """
    Enforces risk limits and autonomy policies.
    Acts as the 'Gatekeeper' for all automated trading actions.
    """

    def __init__(
        self,
        settings_service=None,
        memory_agent: MemoryAgent | None = None,
        message_bus=None,
    ):
        self.logger = logging.getLogger("RiskGuardian")
        self.settings_service = settings_service
        self.memory = memory_agent or MemoryAgent()
        self.message_bus = message_bus

    async def validate_order(
        self,
        tenant_id: str,
        order_payload: dict[str, Any],
        user_preferences: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validates if an order is allowed based on Autonomy & Risk Settings.
        Returns: {"allowed": bool, "reason": str, "requires_approval": bool}
        """
        try:
            # 1. Check Autonomy Status
            autonomy = user_preferences.get("autonomy_status", AutonomyStatus.MANUAL.value)
            risk_settings = user_preferences.get("risk_settings", {})
            profile = RiskProfile(**risk_settings)

            # KILL SWITCH CHECK
            if profile.kill_switch_enabled:
                return {
                    "allowed": False,
                    "reason": "KILL SWITCH ENABLED",
                    "requires_approval": False,
                }

            # 2. Manual Mode -> Always Block, Recommend Approval
            if autonomy == AutonomyStatus.MANUAL.value:
                return {
                    "allowed": False,
                    "reason": "Manual Mode Active - Approval Required",
                    "requires_approval": True,
                }

            # 3. Check Asset Whitelist
            symbol = order_payload.get("symbol")
            if profile.allowed_assets and symbol not in profile.allowed_assets:
                return {
                    "allowed": False,
                    "reason": f"Asset {symbol} not in whitelist",
                    "requires_approval": True,
                }

            # 4. Check Order Size
            amount = order_payload.get("quantity", 0) * order_payload.get("price", 0)
            # Note: Approx value if limit order. For market orders, needs current price.
            # Assuming payload has estimated price.

            if amount > profile.max_order_size:
                return {
                    "allowed": False,
                    "reason": f"Order value (€{amount}) exceeds max limit (€{profile.max_order_size})",
                    "requires_approval": True,
                }

            # 5. Full/Semi Auto Logic
            if autonomy == AutonomyStatus.FULL_AUTO.value:
                return {
                    "allowed": True,
                    "reason": "Risk Checks Passed (Full Auto)",
                    "requires_approval": False,
                }

            elif autonomy == AutonomyStatus.SEMI_AUTO.value:
                # In Semi-Auto, we might allow small trades below a threshold, but for now specific logic:
                # If it passes risk checks, we can allow it OR still require approval.
                # Let's say Semi-Auto allows ONLY if confidence is high (not implemented yet)
                # For now, Semi-Auto still defaults to Approval for anything significant.

                # Simple rule: If value < 10% of max, allow. Else approve.
                if amount < (profile.max_order_size * 0.1):
                    return {
                        "allowed": True,
                        "reason": "Micro-order authorized (Semi-Auto)",
                        "requires_approval": False,
                    }

                return {
                    "allowed": False,
                    "reason": "Semi-Auto confirmation required",
                    "requires_approval": True,
                }

            return {
                "allowed": False,
                "reason": "Unknown State",
                "requires_approval": True,
            }

        except ValidationError as e:
            self.logger.error(f"Risk Profile Validation Error: {e}")
            return {
                "allowed": False,
                "reason": "Invalid Risk Configuration",
                "requires_approval": True,
            }
        except Exception as e:
            self.logger.error(f"Guard Runtime Error: {e}")
            return {
                "allowed": False,
                "reason": f"System Error: {str(e)}",
                "requires_approval": True,
            }

    async def handle_message(self, message: AgentMessage):
        """Handle validation requests from Orchestrator."""
        if message.type == "VALIDATE_ORDER":
            # Extract context
            tenant_id = message.payload.get("tenant_id") or ""
            order = message.payload.get("order") or {}
            prefs = message.payload.get("preferences") or {}

            result = await self.validate_order(tenant_id, order, prefs)

            # Reply to Orchestrator
            response = AgentMessage(
                source="risk_guardian_v1",
                target=message.source,
                type="ORDER_VALIDATION_RESULT",
                payload={"original_msg_id": message.id, "result": result},
            )
            if self.message_bus:
                await self.message_bus(response)
