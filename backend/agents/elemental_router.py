"""
Elemental Router - Signal Distribution System.

Role: Router / Switchboard
Function:
- Routes signals to appropriate elemental agents based on context.
- Manages agent registry.
- Checks agent health/prana before routing.
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio

from backend.agents.elemental_base import ElementalBase

logger = logging.getLogger(__name__)

class ElementalRouter:
    """
    Routes signals within the Elemental System.
    Not an agent itself, but a mechanism (Upaya).
    """
    
    def __init__(self):
        self.agents: Dict[str, ElementalBase] = {}
        self.routes: Dict[str, List[str]] = {
            "market_data": ["air", "water", "earth"], # Data flows to Research, Macro, Valuation
            "strategy_signal": ["fire", "earth"],     # Strategy flows to Risk, Execution
            "risk_alert": ["ether", "earth"],         # Alerts flow to Orchestrator, Execution
            "synthesis": ["air", "water", "earth"]    # Feedback loop
        }

    def register_agent(self, agent: ElementalBase):
        """Register an elemental agent."""
        if not isinstance(agent, ElementalBase):
            raise TypeError(f"Agent {agent} must be instance of ElementalBase")
        self.agents[agent.element] = agent
        logger.info(f"Registered agent: {agent.agent_name} for element {agent.element}")

    async def route_signal(self, signal_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route signal to subscribed agents and aggregate responses.
        """
        targets = self.routes.get(signal_type, [])
        if not targets:
            logger.warning(f"No routes for signal type: {signal_type}")
            return {}

        tasks = []
        active_elements = []
        
        for element in targets:
            agent = self.agents.get(element)
            if agent:
                # Check health/prana before dispatching? 
                # Agent's process_signal handles prana check, but we could optimize.
                tasks.append(agent.process_signal(payload))
                active_elements.append(element)
            else:
                logger.debug(f"Target element {element} not registered")

        if not tasks:
            return {}

        # Parallel execution
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        aggregated = {}
        for element, result in zip(active_elements, results):
            if isinstance(result, Exception):
                logger.error(f"Error routing to {element}: {result}")
                aggregated[element] = {"error": str(result)}
            else:
                aggregated[element] = result
                
        return aggregated

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents."""
        return {
            element: agent.elemental_health_check()
            for element, agent in self.agents.items()
        }
