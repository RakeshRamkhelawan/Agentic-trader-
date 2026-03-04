from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.agents.analyst_agent import AnalystAgent
from backend.agents.data_scout_agent import DataScoutAgent
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.trader_agent import TraderAgent
from backend.core.adapters.system_bridge import CognitiveBridge
from backend.core.schemas.ooda_types import (
    ExecutionOutcome,
    RiskDecision,
)
from backend.execution.order_executor import OrderExecutor
from backend.orchestration.ooda_coordinator import OODALoopCoordinator, TradingMode


@pytest.fixture
def mock_data_source():
    source = Mock()
    source.fetch_ticker = AsyncMock(
        return_value={
            "last": 50000.0,
            "volume": 100.5,
            "bid": 49999.0,
            "ask": 50001.0,
            "timestamp": 1234567890.0,
        }
    )
    source.fetch_orderbook = AsyncMock(
        return_value={"bids": [[49999, 10.0], [49998, 5.0]], "asks": [[50001, 8.0], [50002, 3.0]]}
    )
    source.fetch_funding_rate = AsyncMock(return_value=0.0001)
    return source


@pytest.fixture
def mock_event_bus():
    bus = Mock()
    bus.publish = AsyncMock(return_value="msg-id-123")
    return bus


@pytest.fixture
def mock_cognitive_bridge():
    bridge = Mock(spec=CognitiveBridge)
    bridge.process_observation = AsyncMock(return_value=0.5)  # Neutral by default
    return bridge


@pytest.fixture
def mock_order_executor():
    executor = Mock(spec=OrderExecutor)
    executor.execute_trade = AsyncMock(
        return_value=ExecutionOutcome(
            success=True,
            execution_id="exec-123",
            filled_qty=0.1,
            avg_price=50000.0,
            total_cost=5000.0,
            commission=5.0,
            slippage=0.0,
            execution_time=0.05,  # seconds
            error=None,
            timestamp=1600000000.0,
        )
    )
    return executor


class TestEndToEndFlow:
    """
    End-to-End Integration Tests for the OODA Loop.

    Verifies that the OODACoordinator correctly orchestrates the flow
    between DataScout, Analyst, Trader, RiskManager, and Execution.
    """

    @pytest.mark.asyncio
    async def test_full_bullish_flow_execution(
        self, mock_data_source, mock_event_bus, mock_cognitive_bridge, mock_order_executor
    ):
        """
        Scenario: Strong Bull Market -> Buy Signal -> Risk Approved -> Executed.
        """
        # 1. Setup Agents
        data_scout = DataScoutAgent(data_source=mock_data_source, event_bus=mock_event_bus)
        analyst = AnalystAgent()
        trader = TraderAgent()
        # Fixed init arguments
        risk_manager = RiskManagerAgent(
            max_position_size=10.0, max_leverage=5.0, min_confidence=0.6
        )

        # 2. Setup Coordinator
        coordinator = OODALoopCoordinator(
            data_scout=data_scout,
            analyst=analyst,
            trader=trader,
            risk_manager=risk_manager,
            cognitive_bridge=mock_cognitive_bridge,
            order_executor=mock_order_executor,
            circuit_breaker=None,
            trading_mode=TradingMode.AUTO,
            rag_retriever=None,
        )

        # 3. Mock Data
        mock_data_source.fetch_ticker.return_value = {
            "last": 50000.0,
            "volume": 1000.0,
            "bid": 49990.0,
            "ask": 50010.0,
            "timestamp": 1600000000.0,
        }
        mock_data_source.fetch_orderbook.return_value = {
            "bids": [[49990, 10.0]],
            "asks": [[50010, 10.0]],
        }
        mock_cognitive_bridge.process_observation.return_value = 0.9

        # 4. Patch Analyst to see Bullish Indicators (RSI > 60)
        # We need to ensure _calculate_indicators returns high RSI
        with patch.object(
            analyst,
            "_calculate_indicators",
            return_value={"rsi": 70.0, "macd": 1.0, "volume_ma_ratio": 1.5, "spread_pct": 0.01},
        ):
            # 5. Run Cycle
            result = await coordinator.run_cycle("BTC/USDT", current_price=50000.0)

            # 6. Verification
            assert result["symbol"] == "BTC/USDT"
            assert result["proposal"] is not None
            assert result["proposal"].side == "buy"
            assert result["risk_assessment"].decision == RiskDecision.APPROVE
            assert result["execution"]["status"] == "executed"
            mock_order_executor.execute_trade.assert_called_once()

    @pytest.mark.asyncio
    async def test_bearish_flow_notify_only(
        self, mock_data_source, mock_event_bus, mock_cognitive_bridge, mock_order_executor
    ):
        """
        Scenario: Bear Market -> Sell Signal -> Risk Approved -> Notify Only (No Execution).
        """
        data_scout = DataScoutAgent(data_source=mock_data_source, event_bus=mock_event_bus)
        analyst = AnalystAgent()
        trader = TraderAgent()
        risk_manager = RiskManagerAgent()

        coordinator = OODALoopCoordinator(
            data_scout=data_scout,
            analyst=analyst,
            trader=trader,
            risk_manager=risk_manager,
            cognitive_bridge=mock_cognitive_bridge,
            order_executor=mock_order_executor,
            trading_mode=TradingMode.NOTIFY_ONLY,
        )

        mock_data_source.fetch_ticker.return_value = {
            "last": 40000.0,
            "volume": 500.0,
            "timestamp": 1600000000.0,
        }

        # High confidence in NEGATIVE outlook?
        # Analyst uses this value as MAGNITUDE of confidence.
        # So 0.9 = High Confidence.
        # Combined with Bearish Indicators (RSI 30) -> High Confidence Bearish.
        mock_cognitive_bridge.process_observation.return_value = 0.9

        # Patch Analyst to see Bearish Indicators (RSI < 40)
        with patch.object(
            analyst,
            "_calculate_indicators",
            return_value={"rsi": 30.0, "macd": -1.0, "volume_ma_ratio": 1.5, "spread_pct": 0.01},
        ):
            result = await coordinator.run_cycle("BTC/USDT", current_price=40000.0)

            assert result["mode"] == "notify_only"
            assert result["proposal"] is not None
            assert result["proposal"].side == "sell"
            assert result["risk_assessment"].decision == RiskDecision.APPROVE

            # Execution should be None or skipped
            assert result["execution"] is None or result["execution"].get("status") == "skipped"
            mock_order_executor.execute_trade.assert_not_called()

    @pytest.mark.asyncio
    async def test_risk_rejection_flow(
        self, mock_data_source, mock_event_bus, mock_cognitive_bridge, mock_order_executor
    ):
        """
        Scenario: Bull Market -> Buy Signal -> Risk Rejected (Too Risky).
        """
        data_scout = DataScoutAgent(data_source=mock_data_source, event_bus=mock_event_bus)
        analyst = AnalystAgent()
        trader = TraderAgent()
        risk_manager = RiskManagerAgent(min_confidence=0.99, max_position_size=0.1)

        coordinator = OODALoopCoordinator(
            data_scout=data_scout,
            analyst=analyst,
            trader=trader,
            risk_manager=risk_manager,
            cognitive_bridge=mock_cognitive_bridge,
            order_executor=mock_order_executor,
            trading_mode=TradingMode.AUTO,
        )

        mock_data_source.fetch_ticker.return_value = {
            "last": 50000.0,
            "volume": 1000.0,
            "timestamp": 1600000000.0,
        }
        mock_cognitive_bridge.process_observation.return_value = 0.8

        # Patch Analyst for Bullish
        with patch.object(
            analyst,
            "_calculate_indicators",
            return_value={"rsi": 75.0, "macd": 1.0, "volume_ma_ratio": 1.5, "spread_pct": 0.01},
        ):
            result = await coordinator.run_cycle("BTC/USDT", current_price=50000.0)

            assert result["proposal"] is not None
            assert result["risk_assessment"].decision == RiskDecision.REJECT
            assert result["execution"] is None
            mock_order_executor.execute_trade.assert_not_called()
