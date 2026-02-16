from typing import Any, Dict

from backend.core.agents.base import ElementalAgent, ElementType


class PrithviAgent(ElementalAgent):
    """
    Earth Agent (Prithvi) - Solidity, Stability, Risk.
    Focus: Solvency, hard constraints, capital preservation.
    """

    def __init__(self):
        super().__init__(name="Prithvi", element=ElementType.EARTH)

    def process_cycle(
        self, perception: Dict[str, Any], system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Simple logic for now: Check if risk is too high
        risk_level = perception.get("risk_metrics", {}).get("exposure", 0.0)

        # Earth expends prana to hold ground (resist risk)
        if risk_level > 0.7:
            self.expend_prana(0.05)
            return {"action": "hold", "reason": "High risk exposure", "veto": True}

        self.regenerate_prana(0.01)
        return {"action": "monitor", "reason": "Stable ground", "veto": False}


class JalaAgent(ElementalAgent):
    """
    Water Agent (Jala) - Fluidity, Flow, Liquidity.
    Focus: Order flow, momentum, accumulated volume.
    """

    def __init__(self):
        super().__init__(name="Jala", element=ElementType.WATER)

    def process_cycle(
        self, perception: Dict[str, Any], system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        flow = perception.get("flow_metrics", {}).get("momentum", 0.0)

        # Water flows with momentum
        if abs(flow) > 0.5:
            self.regenerate_prana(0.02)  # Gains energy from flow
            return {"action": "flow", "direction": "long" if flow > 0 else "short"}

        # Stagnation costs energy
        self.expend_prana(0.01)
        return {"action": "wait", "reason": "Low momentum"}


class AgniAgent(ElementalAgent):
    """
    Fire Agent (Agni) - Transformation, Execution, PnL.
    Focus: Trade execution, converting potential to realized PnL.
    """

    def __init__(self):
        super().__init__(name="Agni", element=ElementType.FIRE)

    def process_cycle(
        self, perception: Dict[str, Any], system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        opportunity = perception.get("opportunity_score", 0.0)

        # Fire burns bright when opportunity is high
        if opportunity > 0.8:
            self.expend_prana(0.1)  # Execution is costly
            return {"action": "execute", "urgency": "high"}

        self.regenerate_prana(0.01)
        return {"action": "idle", "reason": "Seeking fuel"}


class VayuAgent(ElementalAgent):
    """
    Air Agent (Vayu) - Movement, Strategy, Volatility.
    Focus: Adjusting strategy parameters, seeking volatility.
    """

    def __init__(self):
        super().__init__(name="Vayu", element=ElementType.AIR)

    def process_cycle(
        self, perception: Dict[str, Any], system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        volatility = perception.get("volatility", 0.0)

        # Air thrives in volatility
        if volatility > 0.5:
            self.regenerate_prana(0.03)
            return {"action": "adjust", "strategy": "dynamic"}

        return {"action": "scan", "reason": "Calm winds"}


class AkashaAgent(ElementalAgent):
    """
    Ether Agent (Akasha) - Space, Context, Correlation.
    Focus: Global context, macro correlations, network health.
    """

    def __init__(self):
        super().__init__(name="Akasha", element=ElementType.ETHER)

    def process_cycle(
        self, perception: Dict[str, Any], system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        network_health = perception.get("system_health", {}).get("network", 1.0)

        if network_health < 0.8:
            self.expend_prana(0.05)  # Hard to maintain space with bad network
            return {"action": "warn", "reason": "Network instability"}

        self.regenerate_prana(0.005)
        return {"action": "observe", "reason": "Clear sky"}
