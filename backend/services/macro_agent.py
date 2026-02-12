import asyncio
import logging
from typing import Dict, Any, Optional
from backend.core.memory_agent import MemoryAgent # GEWIJZIGD
from backend.schemas.agent_messages import AgentMessage # GEWIJZIGD

class MacroAgent:
    """
    Analyzes global market conditions (Interest Rates, DXY, VIX).
    Determines if the environment is Risk-On or Risk-Off.
    Mahabhuta: Water (Flow/Context).
    """
    
    def __init__(self, memory_agent: MemoryAgent = None, message_bus=None):
        self.memory = memory_agent or MemoryAgent()
        self.message_bus = message_bus
        self.logger = logging.getLogger("MacroAgent")

    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages from the orchestrator."""
        self.logger.info(f"Macro Agent received message: {message.type} from {message.source}")
        if message.type == "TIMER_TICK_1HOUR":
            await self.run_cycle()

    async def fetch_macro_data(self) -> Dict[str, float]:
        """
        In production: Fetch from Bloomberg/Fred/Yahoo API.
        For now: Mock values.
        """
        # TODO: Implement real API call
        return {
            "us_10y_yield": 4.0,
            "fear_greed_index": 50,
            "dxy": 100.0
        }

    async def analyze_regime(self, data: Dict[str, float]) -> Dict[str, Any]:
        """Determine regime based on metrics."""
        score = 0.0
        
        # 1. Yields (High yields = bad for risk assets)
        if data["us_10y_yield"] > 4.0:
            score -= 0.5
        elif data["us_10y_yield"] < 3.0:
            score += 0.5
            
        # 2. Fear & Greed (Contrarian indicator or Momentum?)
        # Let's assume Momentum for now: Fear is bad.
        if data["fear_greed_index"] < 30:
            score -= 0.5
        elif data["fear_greed_index"] > 70:
            score += 0.5
            
        # 3. DXY (Dollar strength inversely correlated to crypto)
        if data["dxy"] > 103:
            score -= 0.3
        elif data["dxy"] < 95:
            score += 0.3
            
        regime = "NEUTRAL"
        if score > 0.3:
            regime = "RISK_ON"
        elif score < -0.3:
            regime = "RISK_OFF"
            
        return {
            "regime": regime,
            "score": score,
            "factors": data
        }

    async def run_cycle(self):
        """Analyze and publish."""
        try:
            data = await self.fetch_macro_data()
            analysis = await self.analyze_regime(data)
            
            # 1. Store in Memory
            self.memory.store_thought(
                agent_id="macro_v1",
                text=f"Macro Regime: {analysis['regime']} (Score: {analysis['score']})",
                metadata=analysis
            )
            
            # 2. Publish Signal
            msg = AgentMessage(
                source="macro_v1",
                target="orchestrator_v1",
                type="SIGNAL",
                payload=analysis
            )
            
            self.logger.info(f"🌍 MACRO SIGNAL: {analysis['regime']}")
            
            if self.message_bus:
                if asyncio.iscoroutinefunction(self.message_bus):
                    await self.message_bus(msg)
                else:
                    self.message_bus(msg)
                    
        except Exception as e:
            self.logger.error(f"Macro cycle failed: {e}")

async def main():
    logging.basicConfig(level=logging.INFO)
    agent = MacroAgent()
    while True:
        await agent.run_cycle()
        await asyncio.sleep(3600) # Once per hour

if __name__ == "__main__":
    asyncio.run(main())
