import asyncio
import logging
from typing import Any

from backend.core.memory_agent import MemoryAgent  # GEWIJZIGD
from backend.schemas.agent_messages import AgentMessage  # GEWIJZIGD


class ValuationAgent:
    """
    Analyzes asset pricing models to determine fair value.
    Mahabhuta: Earth (Grounding) / Air (Math).
    """

    def __init__(self, memory_agent: MemoryAgent = None, message_bus=None):
        self.memory = memory_agent or MemoryAgent()
        self.message_bus = message_bus
        self.logger = logging.getLogger("ValuationAgent")

    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages from the orchestrator."""
        self.logger.info(f"Valuation Agent received message: {message.type} from {message.source}")
        if (
            message.type == "MARKET_UPDATE"
        ):  # Let op, dit type is nu gedefinieerd in schemas/agent_messages
            await self.run_cycle()

    async def fetch_market_data(self) -> dict[str, float]:
        """Mock data fetcher."""
        return {"price": 45000.0, "sma_200": 42000.0, "nvt_ratio": 50.0}

    async def analyze_value(self, data: dict[str, float]) -> dict[str, Any]:
        price = data["price"]
        sma = data["sma_200"]
        nvt = data["nvt_ratio"]

        # Mayer Multiple (Price / SMA200)
        mayer_multiple = price / sma if sma > 0 else 0

        valuation = "FAIR"
        score = 0.0

        if mayer_multiple <= 0.8:
            valuation = "UNDERVALUED"
            score = 0.8
        elif mayer_multiple >= 2.4:
            valuation = "OVERVALUED"
            score = -0.8
        elif mayer_multiple >= 1.5:
            valuation = "EXPENSIVE"
            score = -0.4

        # NVT Signal (High NVT = Overvalued network)
        if nvt > 80:
            score -= 0.2

        return {
            "valuation": valuation,
            "mayer_multiple": mayer_multiple,
            "score": score,
        }

    async def run_cycle(self):
        try:
            data = await self.fetch_market_data()
            analysis = await self.analyze_value(data)

            self.memory.store_thought(
                agent_id="valuation_v1",
                text=f"Valuation: {analysis['valuation']} (Mayer: {analysis['mayer_multiple']:.2f})",
                metadata=analysis,
            )

            msg = AgentMessage(
                source="valuation_v1",
                target="orchestrator_v1",
                type="SIGNAL",
                payload=analysis,
            )

            self.logger.info(f"💎 VALUATION SIGNAL: {analysis['valuation']}")

            if self.message_bus:
                if asyncio.iscoroutinefunction(self.message_bus):
                    await self.message_bus(msg)
                else:
                    self.message_bus(msg)

        except Exception as e:
            self.logger.error(f"Valuation cycle failed: {e}")


async def main():
    logging.basicConfig(level=logging.INFO)
    agent = ValuationAgent()
    while True:
        await agent.run_cycle()
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
