"""
OODA Loop Test - LIVE Binance Data + PAPER Trading

This test demonstrates:
- DataScout fetching REAL market data from Binance (via CCXT)
- All agents analyzing REAL data and making decisions
- OrderExecutor in PAPER TRADING mode (no real orders)

Safety: No real money at risk - orders are simulated
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Optional

from backend.agents.analyst_agent import AnalystAgent
from backend.agents.data_scout_agent import DataScoutAgent
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.trader_agent import TraderAgent
from backend.core.schemas.ooda_types import (
    ExecutionOutcome,
    ExecutionPlan,
    MarketRegime,
    Observation,
    Orientation,
    RiskAssessment,
    RiskDecision,
    TradeProposal,
)
from backend.execution.ccxt_adapter import CCXTAdapter
from backend.execution.order_executor import OrderExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class LiveBinanceDataTest:
    """
    OODA Loop Integration Test - Live Binance Data + Paper Trading

    Configuration:
    - DataScout: LIVE Binance data (via CCXT, no keys required)
    - Analyst: Analyzes real data
    - Trader: Makes decisions based on real market conditions
    - RiskManager: Validates proposals
    - OrderExecutor: PAPER TRADING (mock adapter, no real orders)
    """

    def __init__(self, symbol: str = "BTC/USDT"):
        self.symbol = symbol

        # OODA Agents
        self.data_scout: Optional[DataScoutAgent] = None
        self.analyst: Optional[AnalystAgent] = None
        self.trader: Optional[TraderAgent] = None
        self.risk_manager: Optional[RiskManagerAgent] = None
        self.executor: Optional[OrderExecutor] = None

        # CCXT adapter for LIVE data fetching
        self.ccxt_data_adapter: Optional[CCXTAdapter] = None

        # Test state
        self.observation: Optional[Observation] = None
        self.orientation: Optional[Orientation] = None
        self.proposal: Optional[TradeProposal] = None
        self.assessment: Optional[RiskAssessment] = None
        self.outcome: Optional[ExecutionOutcome] = None

    async def initialize_agents(self):
        """Initialize all OODA agents with live data source"""
        logger.info("")
        logger.info("=" * 70)
        logger.info("   OODA LOOP - LIVE BINANCE DATA + PAPER TRADING TEST")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Initializing agents...")
        logger.info("")

        # Initialize CCXT adapter for DATA FETCHING (Binance public API)
        logger.info("[SETUP] Initializing CCXT for Binance market data...")
        self.ccxt_data_adapter = CCXTAdapter(exchange_id="binance")

        logger.info("[SUCCESS] CCXT Adapter for Binance initialized!")
        logger.info("")

        # Phase 1: OBSERVE - DataScout with LIVE Binance data
        self.data_scout = DataScoutAgent(data_source=self.ccxt_data_adapter)  # <- LIVE DATA SOURCE
        logger.info("[SUCCESS] DataScout initialized (LIVE BINANCE DATA)")

        # Phase 2: ORIENT - Analyst
        self.analyst = AnalystAgent()
        logger.info("[SUCCESS] Analyst initialized")

        # Phase 3: DECIDE - Trader
        self.trader = TraderAgent()
        logger.info("[SUCCESS] Trader initialized")

        # Phase 4: HARMONIZE - Risk Manager
        self.risk_manager = RiskManagerAgent()
        logger.info("[SUCCESS] RiskManager initialized")

        # Phase 5: ACT - OrderExecutor (NO adapter = PAPER TRADING)
        self.executor = OrderExecutor(
            exchange_adapter=None,
            max_slippage_bps=50,
            order_timeout=30,  # <- PAPER TRADING MODE
        )
        logger.info("[SUCCESS] OrderExecutor initialized (PAPER TRADING MODE)")
        logger.info("")

    async def run_observe_phase(self) -> Observation:
        """Phase 1: OBSERVE - Fetch LIVE market data from Binance"""
        logger.info("=" * 70)
        logger.info("PHASE 1: OBSERVE (DataScout - LIVE BINANCE DATA)")
        logger.info("=" * 70)
        logger.info("")

        trace_id = f"live-binance-{int(datetime.now(UTC).timestamp())}"

        # Fetch LIVE data from Binance
        observation = await self.data_scout.observe(
            symbol=self.symbol,
            trace_id=trace_id,
            include_orderbook=True,
            include_funding=True,
        )

        logger.info("LIVE Market Observation:")
        logger.info("   Symbol: %s", observation.symbol)
        logger.info("   Price: $%,.2f", observation.price)
        logger.info("   Volume (24h): %,.0f", observation.volume)
        logger.info("   Funding Rate: %.4f%%", observation.funding_rate)

        if observation.orderbook:
            best_bid = observation.orderbook.get("bids", [[0, 0]])[0]
            best_ask = observation.orderbook.get("asks", [[0, 0]])[0]
            logger.info("   Best Bid: $%,.2f (%s BTC)", best_bid[0], best_bid[1])
            logger.info("   Best Ask: $%,.2f (%s BTC)", best_ask[0], best_ask[1])
            logger.info("   Spread: $%.2f", (best_ask[0] - best_bid[0]))

        logger.info("")

        return observation

    async def run_orient_phase(self, observation: Observation) -> Orientation:
        """Phase 2: ORIENT - Analyze LIVE market data"""
        logger.info("=" * 70)
        logger.info("PHASE 2: ORIENT (Analyst)")
        logger.info("=" * 70)
        logger.info("")

        # Convert observation to features/context
        features = {
            "price": observation.price,
            "volume": observation.volume,
            "funding_rate": observation.funding_rate,
        }

        context = {"symbol": observation.symbol, "timestamp": observation.timestamp}

        # Analyze
        analysis = await self.analyst.analyze(features, context)

        # Construct Orientation
        orientation = Orientation(
            symbol=observation.symbol,
            regime=MarketRegime.RANGING,  # Default, would be determined by analysis
            core_sentiment=analysis.get("sentiment", 0.5),
            confidence=analysis.get("confidence", 0.5),
            indicators=analysis.get("indicators", {}),
            rag_context=[],
            timestamp=datetime.now(UTC).timestamp(),
        )

        logger.info("Market Analysis:")
        logger.info("   Regime: %s", orientation.regime.value)
        logger.info("   Core Sentiment: %.1f%%", (orientation.core_sentiment * 100))
        logger.info("   Confidence: %.1f%%", (orientation.confidence * 100))
        logger.info("")

        return orientation

    async def run_decide_phase(
        self, orientation: Orientation, current_price: float
    ) -> TradeProposal:
        """Phase 3: DECIDE - Generate trade proposal"""
        logger.info("=" * 70)
        logger.info("PHASE 3: DECIDE (Trader)")
        logger.info("=" * 70)
        logger.info("")

        proposal = await self.trader.propose_trade(
            orientation=orientation,
            current_price=current_price,
            strategy_id="live_momentum_v1",
        )

        if proposal is None:
            logger.info("[INFO] No trade signal - creating demo proposal")
            proposal = TradeProposal(
                symbol=orientation.symbol,
                side="buy",
                size=0.001,
                entry_price=current_price,
                stop_loss=current_price * 0.98,
                take_profit=current_price * 1.05,
                confidence=0.65,
                rationale="Demo trade proposal based on live Binance data",
                strategy_id="live_demo",
            )

        logger.info("Trade Proposal:")
        logger.info("   Symbol: %s", proposal.symbol)
        logger.info("   Side: %s", proposal.side.upper())
        logger.info("   Size: %s", proposal.size)
        logger.info("   Entry Price: $%,.2f", proposal.entry_price)
        logger.info(
            "   Stop Loss: $%,.2f (%+.1f%%)",
            proposal.stop_loss,
            ((proposal.stop_loss / proposal.entry_price - 1) * 100),
        )
        logger.info(
            "   Take Profit: $%,.2f (%+.1f%%)",
            proposal.take_profit,
            ((proposal.take_profit / proposal.entry_price - 1) * 100),
        )
        logger.info("   Confidence: %.1f%%", (proposal.confidence * 100))
        logger.info("   Rationale: %s", proposal.rationale)
        logger.info("")

        return proposal

    async def run_harmonize_phase(
        self, proposal: TradeProposal, regime: MarketRegime
    ) -> RiskAssessment:
        """Phase 4: HARMONIZE - Risk assessment"""
        logger.info("=" * 70)
        logger.info("PHASE 4: HARMONIZE (Risk Manager)")
        logger.info("=" * 70)
        logger.info("")

        assessment = await self.risk_manager.assess_risk(
            proposal=proposal,
            current_regime=regime,
            current_position_size=0.0,  # No open positions
        )

        logger.info("Risk Assessment:")
        logger.info("   Decision: %s", assessment.decision.value.upper())
        logger.info("   Risk Score: %.2f", assessment.risk_score)
        logger.info("   Win Probability: %.0f%%", (assessment.win_probability * 100))
        logger.info("   Rationale: %s", assessment.rationale)
        logger.info("")

        if assessment.decision == RiskDecision.APPROVE:
            logger.info("[APPROVED] Trade approved - proceeding to execution...")
        else:
            logger.info("[REJECTED] Trade rejected by Risk Manager")

        logger.info("")

        return assessment

    async def run_act_phase(
        self, proposal: TradeProposal, assessment: RiskAssessment
    ) -> Optional[ExecutionOutcome]:
        """Phase 5: ACT - Execute trade (PAPER TRADING)"""
        logger.info("=" * 70)
        logger.info("PHASE 5: ACT (Order Executor - PAPER TRADING)")
        logger.info("=" * 70)
        logger.info("")

        if assessment.decision != RiskDecision.APPROVE:
            logger.info("[SKIP] Trade not approved - no execution")
            logger.info("")
            return None

        # Create execution plan
        execution_plan = ExecutionPlan(
            symbol=proposal.symbol,
            side=proposal.side,
            quantity=proposal.size,
            order_type="limit",
            price=proposal.entry_price,
            expected_price=proposal.entry_price,
            trace_id=f"live-paper-{int(datetime.now(UTC).timestamp())}",
            caller_name="live_data_paper_test",
            caller_role="executor",
        )

        logger.info("Executing PAPER trade...")

        # Execute (paper trading - no real order)
        outcome = await self.executor.execute_trade(execution_plan)

        logger.info("Paper Trade Outcome:")
        logger.info("   Success: %s", outcome.success)
        logger.info("   Filled Qty: %s", outcome.filled_qty)
        logger.info("   Avg Price: $%,.2f", outcome.avg_price)

        if outcome.success:
            logger.info("   [SUCCESS] PAPER TRADE COMPLETED")
        else:
            logger.info("   [ERROR] %s", outcome.error)

        logger.info("")

        return outcome

    async def run_full_cycle(self):
        """Execute complete OODA cycle with live data"""
        try:
            # Initialize
            await self.initialize_agents()

            # Phase 1: OBSERVE (LIVE DATA)
            self.observation = await self.run_observe_phase()

            # Phase 2: ORIENT
            self.orientation = await self.run_orient_phase(self.observation)

            # Phase 3: DECIDE
            self.proposal = await self.run_decide_phase(self.orientation, self.observation.price)

            # Phase 4: HARMONIZE
            self.assessment = await self.run_harmonize_phase(self.proposal, self.orientation.regime)

            # Phase 5: ACT (PAPER TRADING)
            self.outcome = await self.run_act_phase(self.proposal, self.assessment)

            # Summary
            logger.info("=" * 70)
            logger.info("OODA CYCLE COMPLETED")
            logger.info("=" * 70)
            logger.info("")
            logger.info("[SUCCESS] Summary:")
            logger.info("   Data Source: LIVE BINANCE")
            logger.info(
                "   Market: %s @ $%,.2f",
                self.observation.symbol,
                self.observation.price,
            )
            logger.info("   Decision: %s", self.proposal.side.upper())
            logger.info("   Risk Decision: %s", self.assessment.decision.value)
            logger.info(
                "   Paper Trade: %s",
                ("Success" if self.outcome and self.outcome.success else "Skipped/Failed"),
            )
            logger.info("")

        except Exception as e:
            logger.error("[ERROR] OODA cycle failed: %s", e)
            import traceback

            logger.error(traceback.format_exc())
            raise

        finally:
            # Cleanup
            if self.ccxt_data_adapter:
                await self.ccxt_data_adapter.disconnect()
                logger.info("[CLEANUP] Disconnected from CCXT")


async def main():
    """Run the test"""
    test = LiveBinanceDataTest(symbol="BTC/USDT")
    await test.run_full_cycle()


if __name__ == "__main__":
    # Ensure CCXT is installed
    try:
        import ccxt
        import ccxt.pro
    except ImportError:
        print("=" * 70)
        print("ERROR: CCXT library not found.")
        print("Please install it: pip install ccxt[pro]")
        print("=" * 70)
        exit(1)

    asyncio.run(main())
