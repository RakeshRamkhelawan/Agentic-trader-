from datetime import datetime
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from backend.core.execution.audit_logger import ExecutionAudit
from backend.core.execution.rahu_kala_gate import RahuKalaGate
from backend.core.execution.smart_router import SmartRouter
from backend.core.karma.karma_register import KarmaRegister, TradeOutcome
from backend.core.risk.guna_sizing import GunaType
from backend.core.risk.mifid_checks import (
    ClientClassification,
    ClientProfile,
    TradeRequest,
)
from backend.core.risk.risk_manager import RiskManager
from backend.core.strategy.pattern_detector import PatternDetector


@pytest.mark.asyncio
class TestIntegrationPipeline:
    """
    End-to-End Integration Test for the Prithvi Agent Backend Pipeline.
    Simulates: Data -> Orient -> Decide -> Act -> Feedback
    """

    async def test_full_trade_lifecycle(self):
        # ============================================================================
        # 1. SETUP & MOCKS
        # ============================================================================

        # Mock Client Profile (Professional, High Knowledge)
        profile = ClientProfile(
            client_id="client_001",
            classification=ClientClassification.PROFESSIONAL,
            knowledge_score=10,
            experience_years=5,
            max_loss_tolerance_pct=0.20,
            current_drawdown_pct=0.05,
        )

        # Mock Market Data (Downtrend to trigger RSI Oversold -> Bullish Reversal)
        dates = pd.date_range(start="2024-01-01", periods=50, freq="1H")
        # Create a price series that drops (Downtrend)
        prices = np.linspace(150, 100, 50)
        df = pd.DataFrame(
            {
                "open": prices,
                "high": prices + 1,
                "low": prices - 1,
                "close": prices,
                "volume": 1000,
            },
            index=dates,
        )

        # Initialize Cores
        detector = PatternDetector()
        risk_manager = RiskManager()
        router = SmartRouter()
        gate = RahuKalaGate()
        audit = ExecutionAudit()
        karma = KarmaRegister()

        # ============================================================================
        # 2. ORIENT (Strategy)
        # ============================================================================
        # Detect patterns in market data
        signals = detector.analyze(df)

        # We constructed linear growth, so SMA(20) < Price should be true (Bullish Trend)
        # Check if we have a bullish signal
        # PatternSignal has fields: pattern, signal, confidence
        bullish_signal = next((s for s in signals if s.signal == "bullish"), None)
        assert (
            bullish_signal is not None
        ), "Pipeline Validation Failed: Strategy Core did not detect bullish trend."

        print(
            f"[ORIENT] Signal Detected: {bullish_signal.signal} ({bullish_signal.confidence} conf)"
        )

        # ============================================================================
        # 3. DECIDE (Risk)
        # ============================================================================
        # Construct Trade Request based on signal
        # Note: Strategy ID is not part of TradeRequest model currently,
        # so we track it separately or extend the model later.

        request = TradeRequest(
            asset="BTC/USD",
            amount=1.0,
            side="buy",  # TradeSide enum not strictly enforced in model yet, string "buy"
            price=50000.0,  # Estimated price for risk check
            notional_value=50000.0 * 1.0,
        )

        # Inject Guna Context (Sattva = Balanced/Clear)
        current_guna = GunaType.SATTVA

        # Evaluate Risk
        decision = risk_manager.evaluate_trade(profile, request, current_guna)

        assert (
            decision.decision == "accept"
        ), f"Pipeline Validation Failed: Risk Core rejected trade. Reason: {decision.reason}"
        assert (
            decision.adjusted_size == 1.0
        ), "Pipeline Validation Failed: Guna Sizer (Sattva) should not reduce size."

        print(f"[DECIDE] Risk Approved: {decision.reason} | Size: {decision.adjusted_size}")

        # ============================================================================
        # 4. ACT (Execution)
        # ============================================================================

        # 4a. Time Gate (Rahu Kala)
        # Mock time to be SAFE (Not Rahu Kala)
        with patch(
            "backend.core.execution.rahu_kala_gate.RahuKalaGate.is_in_rahu_kala",
            return_value=False,
        ):
            can_execute = gate.can_enter_trade(datetime.now())
            assert (
                can_execute is True
            ), "Pipeline Validation Failed: Rahu Kala Gate blocked trade during safe time."
            print("[ACT] Rahu Kala Gate: OPEN (Safe to trade)")

        # 4b. Smart Routing
        # Mock exchange quotes

        # Note: SmartRouter uses get_best_route(asset, side, amount)
        # We patch _fetch_quotes or just the internal logic if needed,
        # but here we are integration testing the router logic itself too (with mocked quotes).
        # We need to patch the internal quote fetching if we want to force a winner,
        # OR we can trust the logic if we provide the right mock data structure
        # if the router implementation exposes a way to inject them.
        # Looking at SmartRouter, it hardcodes mocks in get_best_route for now (POC phase).
        # So we just call it and expect the hardcoded "binance" win if that matches logic,
        # OR we patch the hardcoded values if possible (harder).
        # Actually, the SmartRouter implementation I saw HAS hardcoded mock_prices inside the method.
        # So I will assert based on THAT implementation for now (Kraken 50k, Binance 50010, Coinbase 49990).
        # Wait, if side="buy", lower is better. Coinbase is 49990.
        # Let's see what the SmartRouter implementation I viewed actually does.
        # Coinbase: 49990. Binance: 50010. Kraken: 50000.
        # Coinbase fee: 0.0060 (0.6%). Effective: 49990 * 1.006 = 50289.
        # Binance fee: 0.0010 (0.1%). Effective: 50010 * 1.001 = 50060.
        # Kraken fee: 0.0026 (0.26%). Effective: 50000 * 1.0026 = 50130.
        # Winner should be Binance (50060 is lowest effective buy price).

        route = await router.get_best_route(request.asset, request.side, request.amount)

        assert (
            route.selected_exchange_id == "binance"
        ), f"Pipeline Validation Failed: Smart Router selected {route.selected_exchange_id}, expected binance."
        print(f"[ACT] Routed to: {route.selected_exchange_id} @ {route.price}")

        # 4c. Execution Audit
        log_entry = audit.log_event(
            event_type="FILLED",
            details={"venue": route.selected_exchange_id, "price": route.price},
            correlation_id="trade_integration_001",
        )
        assert (
            log_entry["event_type"] == "FILLED"
        ), "Pipeline Validation Failed: Audit Logger failed."

        # ============================================================================
        # 5. FEEDBACK (Karma)
        # ============================================================================
        # Simulate Outcome (Profit)
        # TradeOutcome expects pnl_percent, drawdown_percent, execution_speed_ms
        outcome = TradeOutcome(
            pnl_percent=0.05,  # 5% Profit
            drawdown_percent=0.01,  # 1% Drawdown
            execution_speed_ms=120,
        )

        # KarmaRegister expects (agent_name, outcome)
        # integration_agent is our mock agent
        karma_score = karma.register_feedback("integration_agent", outcome)

        assert (
            karma_score > 0
        ), "Pipeline Validation Failed: Positive PnL should yield Positive Karma."
        print(f"[FEEDBACK] Karma Score: {karma_score}")

        print("\n✅ INTEGRATION PIPELINE TEST PASSED SUCCESSFULLY")
