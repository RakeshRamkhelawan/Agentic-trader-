"""
PortfolioManagerAgent - OODA wrapper for PortfolioManager.

Provides multi-exchange portfolio aggregation as an agent service.
Integrates with FundManagerAgent for capital allocation decisions.

Week 1 of Exchange Integration Refactor.
"""

from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.schemas.ooda_types import PortfolioState
from backend.execution.portfolio_manager import PortfolioManager, get_portfolio_manager


class PortfolioManagerAgent(BaseAgent):
    """
    Agent wrapper for multi-exchange portfolio management.

    Extends BaseAgent to participate in OODA loop while
    providing cross-exchange portfolio visibility.

    Example:
        >>> agent = PortfolioManagerAgent(event_bus=event_bus)
        >>> await agent.initialize_adapters()
        >>> portfolio = await agent.get_portfolio_state()
        >>> print(f"Total equity: ${portfolio.total_equity}")
    """

    def __init__(
        self,
        llm_provider: Any | None = None,
        event_bus: Any | None = None,
        portfolio_manager: PortfolioManager | None = None,
    ):
        """
        Initialize PortfolioManagerAgent.

        Args:
            llm_provider: Optional LLM for reasoning
            event_bus: Event bus for publishing updates
            portfolio_manager: Optional PortfolioManager instance
        """
        super().__init__(
            agent_name="PortfolioManager",
            llm_provider=llm_provider,
            event_bus=event_bus,
        )

        # Use provided manager or create new
        self.portfolio_manager = portfolio_manager or get_portfolio_manager()
        self._adapters_initialized = False

        self.logger.info("[PortfolioManagerAgent] Initialized")

    async def initialize_adapters(self) -> None:
        """Initialize and register exchange adapters."""
        if self._adapters_initialized:
            return

        from backend.core.config.settings import settings

        # Initialize Bitvavo if configured
        if settings.BITVAVO_API_KEY:
            try:
                from backend.execution.bitvavo_adapter import BitvavoAdapter

                bitvavo = BitvavoAdapter()
                if await bitvavo.initialize():
                    self.portfolio_manager.register_adapter("bitvavo", bitvavo)
                    self.logger.info("[PortfolioManagerAgent] Bitvavo adapter registered")
            except Exception as e:
                self.logger.error(f"[PortfolioManagerAgent] Failed to initialize Bitvavo: {e}")

        # Initialize Revolut if configured
        if settings.REVOLUT_API_KEY:
            try:
                from backend.execution.revolut_x_adapter import RevolutXAdapter

                revolut = RevolutXAdapter()
                if await revolut.connect():
                    self.portfolio_manager.register_adapter("revolut", revolut)
                    self.logger.info("[PortfolioManagerAgent] Revolut adapter registered")
            except Exception as e:
                self.logger.error(f"[PortfolioManagerAgent] Failed to initialize Revolut: {e}")

        self._adapters_initialized = True

    async def analyze(self, features: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze portfolio state (ReAct pattern).

        Args:
            features: Input features
            context: Analysis context

        Returns:
            Portfolio analysis for other agents
        """
        self.heartbeat()

        await self.initialize_adapters()

        try:
            # Get portfolio state
            portfolio = await self.portfolio_manager.get_portfolio_state()

            # Analyze allocation
            analysis = {
                "total_equity": portfolio.total_equity,
                "available_capital": portfolio.available_capital,
                "exposure_pct": portfolio.total_exposure_pct,
                "open_positions": portfolio.num_open_positions,
                "risk_level": self._assess_risk_level(portfolio),
                "can_trade": portfolio.available_capital > 1000,  # Min $1000
            }

            # Publish thought
            await self.publish_thought(
                reasoning=f"Portfolio exposure: {portfolio.total_exposure_pct:.1%}, "
                f"Available: ${portfolio.available_capital:,.2f}, "
                f"Risk level: {analysis['risk_level']}",
                confidence=0.95,
                data=analysis,
            )

            return analysis

        except Exception as e:
            self.logger.error(f"[PortfolioManagerAgent] Analysis failed: {e}")
            return {"error": str(e), "can_trade": False}

    async def get_portfolio_state(self) -> PortfolioState:
        """
        Get OODA-compatible portfolio state.

        Returns:
            PortfolioState for FundManagerAgent
        """
        await self.initialize_adapters()
        return await self.portfolio_manager.get_portfolio_state()

    async def get_portfolio_report(self) -> str:
        """Get formatted portfolio report."""
        await self.initialize_adapters()
        return self.portfolio_manager.get_allocation_report()

    def _assess_risk_level(self, portfolio: PortfolioState) -> str:
        """
        Assess portfolio risk level.

        Args:
            portfolio: Portfolio state

        Returns:
            Risk level: "low", "medium", "high"
        """
        if portfolio.total_exposure_pct > 0.8:
            return "high"
        elif portfolio.total_exposure_pct > 0.5:
            return "medium"
        return "low"

    async def can_allocate(self, amount_usd: float) -> bool:
        """
        Check if amount can be allocated.

        Args:
            amount_usd: Amount to allocate

        Returns:
            True if allocation possible
        """
        await self.initialize_adapters()

        portfolio = await self.get_portfolio_state()
        return portfolio.available_capital >= amount_usd


# Factory function
def get_portfolio_manager_agent(event_bus: Any | None = None) -> PortfolioManagerAgent:
    """Get or create PortfolioManagerAgent."""
    return PortfolioManagerAgent(event_bus=event_bus)
