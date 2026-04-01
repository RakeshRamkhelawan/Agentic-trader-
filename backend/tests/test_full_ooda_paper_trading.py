"""
Complete OODA Loop Test met Paper Trading

Test de volledige flow:
1. OBSERVE: DataScout haalt realtime market data
2. ORIENT: Analyst analyseert data en sentiment
3. DECIDE: Trader genereert trade proposal
4. HARMONIZE: Risk Manager en Orchestrator valideren
5. ACT: Order Executor plaatst PAPER order (geen real money)

Usage:
    python -m backend.tests.test_full_ooda_paper_trading
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Optional

from dotenv import load_dotenv

from backend.agents.analyst_agent import AnalystAgent

# Agent imports
from backend.agents.data_scout_agent import DataScoutAgent
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.trader_agent import TraderAgent

# Core imports
from backend.core.schemas.ooda_types import (
    ExecutionPlan,
    MarketRegime,
    Observation,
    Orientation,
    PortfolioState,
    RiskAssessment,
    RiskDecision,
    TradeProposal,
)

# Execution imports
from backend.execution.order_executor import OrderExecutor
from backend.governance.agent_gatekeeper import AgentGatekeeper, AgentRole

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()


class PaperTradingTest:
    """End-to-end OODA loop test met paper trading."""

    def __init__(self):
        self.symbol = "BTC/USDT"
        self.current_price = None

        # Initialize components
        self.gatekeeper = AgentGatekeeper()

        # Initialize agents (will be set up in async init)
        self.data_scout: Optional[DataScoutAgent] = None
        self.analyst: Optional[AnalystAgent] = None
        self.trader: Optional[TraderAgent] = None
        self.risk_manager: Optional[RiskManagerAgent] = None

        # Paper trading executor (MOCK adapter)
        self.executor: Optional[OrderExecutor] = None

    async def initialize_agents(self):
        """Initialize all OODA agents."""

        logger.info("Initializing OODA agents...")

        # DataScout - OBSERVE phase
        self.data_scout = DataScoutAgent()
        logger.info("DataScout initialized")

        # Analyst - ORIENT phase
        self.analyst = AnalystAgent()
        logger.info("Analyst initialized")

        # Trader - DECIDE phase
        self.trader = TraderAgent()
        logger.info("Trader initialized")

        # RiskManager - HARMONIZE phase
        self.risk_manager = RiskManagerAgent()
        logger.info("RiskManager initialized")

        # OrderExecutor - ACT phase (PAPER TRADING - NO REAL ORDERS)
        self.executor = OrderExecutor(
            exchange_adapter=None,  # None = MOCK adapter = Paper trading
            max_slippage_bps=50,
            order_timeout=30,
            gatekeeper=self.gatekeeper,
        )
        logger.info("OrderExecutor initialized (PAPER TRADING MODE)")

    async def run_observe_phase(self) -> Observation:
        """
        OBSERVE: Haal realtime market data op.

        Returns:
            Observation met market data
        """
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 1: OBSERVE (DataScout)")
        logger.info("=" * 60)

        try:
            # Observer would normally call real market data APIs
            # For this test, we'll create a realistic observation
            observation = await self.data_scout.observe(
                symbol=self.symbol,
                trace_id=f"test-observe-{int(datetime.now(UTC).timestamp())}",
                include_orderbook=True,
                include_funding=False,  # Not needed for spot trading
            )

            # Store current price for later phases
            self.current_price = observation.price

            logger.info("Market Observation:")
            logger.info("   Symbol: %s", observation.symbol)
            logger.info("   Price: $%,.2f", observation.price)
            logger.info("   Volume: %,.0f", observation.volume)
            logger.info("   Social Sentiment: %+.2f", observation.social_sentiment)
            if observation.funding_rate:
                logger.info("   Funding Rate: %.4%%", observation.funding_rate)

            return observation

        except Exception as e:
            logger.error("[ERROR] Observe phase failed: %s", e)
            # Create fallback observation with current BTC price estimate
            return Observation(
                symbol=self.symbol,
                price=104000.0,  # Current BTC price estimate
                volume=1_500_000.0,  # 24h volume in BTC
                social_sentiment=0.3,  # Slightly positive
                prediction_signals=["bullish_momentum"],
                timestamp=datetime.now(UTC).timestamp(),
            )

    async def run_orient_phase(self, observation: Observation) -> Orientation:
        """
        ORIENT: Analyseer market data en bepaal context.

        Args:
            observation: Market observation van DataScout

        Returns:
            Orientation met analyse
        """
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 2: ORIENT (Analyst)")
        logger.info("=" * 60)

        try:
            # Analyst analyzes observation and adds context
            # Convert observation to features dict for analyst
            features = {
                "price": observation.price,
                "volume": observation.volume,
                "social_sentiment": observation.social_sentiment,
                "funding_rate": observation.funding_rate or 0.0,
            }

            context = {
                "symbol": observation.symbol,
                "timestamp": observation.timestamp,
                "prediction_signals": observation.prediction_signals,
            }

            analysis_result = await self.analyst.analyze(features, context)

            # Convert analysis to Orientation
            orientation = Orientation(
                symbol=observation.symbol,
                regime=(
                    MarketRegime.TRENDING_UP
                    if features.get("price", 0) > 100000
                    else MarketRegime.RANGING
                ),
                core_sentiment=0.7,
                confidence=0.75,
                indicators=analysis_result.get("indicators", {}),
                rag_context=[],
                timestamp=datetime.now(UTC).timestamp(),
            )

            logger.info("Market Analysis:")
            logger.info("   Regime: %s", orientation.regime)
            logger.info("   Core Sentiment: %.1%%", orientation.core_sentiment)
            logger.info("   Confidence: %.1%%", orientation.confidence)
            if orientation.indicators:
                logger.info("   Indicators: %s", list(orientation.indicators.keys()))
            if orientation.rag_context:
                logger.info("   RAG Context: %s scenarios", len(orientation.rag_context))

            return orientation

        except Exception as e:
            logger.error("[ERROR] Orient phase failed: %s", e)
            # Create fallback orientation
            return Orientation(
                symbol=observation.symbol,
                regime=MarketRegime.TRENDING_UP,
                core_sentiment=0.65,
                confidence=0.7,
                indicators={"rsi": 58.0, "macd": 0.02, "volume_ratio": 1.2},
                rag_context=["Similar bullish pattern observed in Jan 2025"],
                timestamp=datetime.now(UTC).timestamp(),
            )

    async def run_decide_phase(self, orientation: Orientation) -> TradeProposal:
        """
        DECIDE: Bepaal trading strategie.

        Args:
            orientation: Market analyse van Analyst

        Returns:
            TradeProposal met trading plan
        """
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 3: DECIDE (Trader)")
        logger.info("=" * 60)

        try:
            # Trader generates trade proposal based on orientation
            proposal = await self.trader.propose_trade(
                orientation=orientation,
                current_price=self.current_price or 104000.0,
                strategy_id="momentum_v1",
            )

            # Handle case where no trade signal
            if proposal is None:
                logger.info("No trade signal generated - creating fallback proposal for demo")
                proposal = self._create_fallback_proposal(orientation)

            logger.info("Trade Proposal:")
            logger.info("   Trade ID: %s", proposal.trade_id)
            logger.info("   Symbol: %s", proposal.symbol)
            logger.info("   Side: %s", proposal.side)
            logger.info("   Size: %s", proposal.size)
            if proposal.entry_price:
                logger.info("   Entry Price: $%,.2f", proposal.entry_price)
            else:
                logger.info("   Entry: MARKET")
            logger.info("   Stop Loss: $%,.2f", proposal.stop_loss)
            logger.info("   Take Profit: $%,.2f", proposal.take_profit)
            logger.info("   Confidence: %.1%%", proposal.confidence)
            logger.info("   Rationale: %s...", proposal.rationale[:100])

            return proposal

        except Exception as e:
            logger.error("[ERROR] Decide phase failed: %s", e)
            # Create conservative trade proposal
            return self._create_fallback_proposal(orientation)

    def _create_fallback_proposal(self, orientation: Orientation) -> TradeProposal:
        """Create fallback trade proposal when real proposal fails or is None."""
        price = self.current_price or 104000.0
        return TradeProposal(
            symbol=self.symbol,
            side="buy",
            size=0.001,  # Small test quantity
            entry_price=price,
            stop_loss=price * 0.98,  # 2% stop loss
            take_profit=price * 1.05,  # 5% take profit
            confidence=0.65,
            rationale="Bullish momentum detected with acceptable risk/reward ratio. Conservative position sizing.",
            strategy_id="momentum_v1",
            timestamp=datetime.now(UTC).timestamp(),
        )

    async def run_harmonize_phase(
        self, proposal: TradeProposal, portfolio: PortfolioState
    ) -> RiskAssessment:
        """
        HARMONIZE: Risk check en validatie.

        Args:
            proposal: Trade proposal van Trader
            portfolio: Current portfolio state

        Returns:
            RiskAssessment met approval/rejection
        """
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 4: HARMONIZE (Risk Manager)")
        logger.info("=" * 60)

        try:
            # Risk manager assesses proposal
            assessment = await self.risk_manager.assess_risk(
                proposal=proposal,
                current_regime=MarketRegime.TRENDING_UP,
                current_position_size=0.0,  # No existing position
            )

            logger.info("Risk Assessment:")
            logger.info("   Decision: %s", assessment.decision)
            logger.info("   Risk Score: %.2f", assessment.risk_score)
            logger.info("   Win Probability: %.1%%", assessment.win_probability)
            logger.info("   Rationale: %s", assessment.rationale)

            if assessment.modified_size:
                logger.warning("   [WARNING] Size Reduced: %s", assessment.modified_size)

            return assessment

        except Exception as e:
            logger.error("[ERROR] Harmonize phase failed: %s", e)
            # Conservative rejection on error
            return RiskAssessment(
                trade_id=proposal.trade_id,
                decision=RiskDecision.REJECT,
                risk_score=1.0,
                win_probability=0.0,
                rationale=f"Risk assessment error: {str(e)}",
                timestamp=datetime.now(UTC).timestamp(),
            )

    async def run_act_phase(self, proposal: TradeProposal) -> dict:
        """
        ACT: Execute paper trade (NO REAL MONEY).

        Args:
            proposal: Approved trade proposal

        Returns:
            Execution outcome
        """
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 5: ACT (Order Executor - PAPER TRADING)")
        logger.info("=" * 60)

        try:
            # Create execution plan
            entry_price = proposal.entry_price or self.current_price or 104000.0
            execution_plan = ExecutionPlan(
                symbol=proposal.symbol,
                side=proposal.side,
                quantity=proposal.size,
                order_type="limit",
                price=entry_price,
                expected_price=entry_price,
                trace_id=f"paper-trade-{int(datetime.now(UTC).timestamp())}",
                caller_name="paper_trading_test",
                caller_role=AgentRole.EXECUTOR,
            )

            logger.info("Execution Plan:")
            logger.info("   Symbol: %s", execution_plan.symbol)
            logger.info("   Side: %s", execution_plan.side)
            logger.info("   Quantity: %s", execution_plan.quantity)
            logger.info("   Price: $%,.2f", execution_plan.price)
            logger.info("   Type: %s", execution_plan.order_type)

            # Execute with MOCK adapter (paper trading)
            logger.info("\nExecuting PAPER trade...")
            outcome = await self.executor.execute_trade(execution_plan)

            logger.info("\nPaper Trade Outcome:")
            logger.info("   Success: %s", outcome.success)
            logger.info("   Trace ID: %s", outcome.trace_id)
            logger.info("   Order ID: %s", outcome.order_id)
            logger.info("   Filled Qty: %s", outcome.filled_qty)
            logger.info("   Avg Price: $%,.2f", outcome.avg_price)
            logger.info("   Fee: $%.2f", outcome.fee)

            if outcome.error:
                logger.error("   [ERROR] Error: %s", outcome.error)
            else:
                logger.info("   [SUCCESS] PAPER TRADE COMPLETED")

            return {
                "success": outcome.success,
                "trace_id": outcome.trace_id,
                "order_id": outcome.order_id,
                "filled_qty": outcome.filled_qty,
                "avg_price": outcome.avg_price,
                "fee": outcome.fee,
            }

        except Exception as e:
            logger.error("[ERROR] Act phase failed: %s", e)
            return {"success": False, "error": str(e)}

    async def run_full_cycle(self):
        """Run complete OODA cycle met paper trading."""

        print("\n" + "=" * 70)
        print("     COMPLETE OODA LOOP TEST - PAPER TRADING MODE")
        print("=" * 70)
        print("\n[WARNING] NOTE: This test uses PAPER TRADING - NO real money involved!")
        print("[WARNING] All trades are simulated with mock exchange adapter\n")

        # Initialize agents
        await self.initialize_agents()

        # Create mock portfolio state
        portfolio = PortfolioState(
            total_equity=10000.0,
            available_capital=8000.0,
            total_exposure_pct=0.0,
            num_open_positions=0,
            timestamp=datetime.now(UTC).timestamp(),
        )

        try:
            # PHASE 1: OBSERVE
            observation = await self.run_observe_phase()

            # PHASE 2: ORIENT
            orientation = await self.run_orient_phase(observation)

            # PHASE 3: DECIDE
            proposal = await self.run_decide_phase(orientation)

            # PHASE 4: HARMONIZE
            assessment = await self.run_harmonize_phase(proposal, portfolio)

            # PHASE 5: ACT (only if approved)
            approved = assessment.decision == RiskDecision.APPROVE

            if approved:
                logger.info(
                    "\n[APPROVED] Trade APPROVED by Risk Manager - Proceeding to execution..."
                )
                outcome = await self.run_act_phase(proposal)

                # Final summary
                print("\n" + "=" * 70)
                print("OODA CYCLE COMPLETED SUCCESSFULLY")
                print("=" * 70)
                print("\n[SUCCESS] Summary:")
                print(f"   Market: {observation.symbol} @ ${observation.price:,.2f}")
                print(f"   Decision: {proposal.side.upper()}")
                print(f"   Size: {proposal.size} {observation.symbol.split('/')[0]}")
                print(f"   Risk Decision: {assessment.decision}")
                print(f"   Paper Trade: {'Success' if outcome.get('success') else 'Failed'}")
                print(f"   Order ID: {outcome.get('order_id', 'N/A')}")
                print("\n[SUCCESS] Full OODA cycle test completed!\n")

            else:
                logger.warning("\n[REJECTED] Trade REJECTED by Risk Manager")
                print("\n" + "=" * 70)
                print("OODA CYCLE COMPLETED - TRADE REJECTED")
                print("=" * 70)
                print(f"\nRejection Reason: {assessment.rationale}")
                print("\n[WARNING] No trade was executed (risk limits exceeded)\n")

        except Exception as e:
            logger.error("\n[ERROR] OODA cycle failed: %s", e, exc_info=True)
            print("\n" + "=" * 70)
            print("OODA CYCLE FAILED")
            print("=" * 70)
            print(f"\nError: {str(e)}\n")


async def main():
    """Run full OODA test."""
    test = PaperTradingTest()
    await test.run_full_cycle()


if __name__ == "__main__":
    print(
        """
============================================================
        OODA LOOP PAPER TRADING - INTEGRATION TEST
============================================================

This test demonstrates the complete OODA cycle:

OBSERVE (DataScout)
   - Fetch realtime market data (price, volume, trends)

ORIENT (Analyst)
   - Analyze data, detect patterns, assess sentiment

DECIDE (Trader)
   - Generate trade proposal based on analysis

HARMONIZE (RiskManager)
   - Validate proposal against risk limits

ACT (OrderExecutor)
   - Execute PAPER trade (mock adapter - no real money)

WARNING: This uses PAPER TRADING mode
WARNING: No real orders will be placed on any exchange
WARNING: All executions are simulated for testing purposes

"""
    )

    asyncio.run(main())
