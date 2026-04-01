"""
Phase C Unit Tests: Wire Risk Pipeline

Tests voor RiskOrchestrator als Kanchuka-laag:
- Pre-trade risk checks
- Drawdown monitor kill switch
- Position sizing integratie
"""

from unittest.mock import MagicMock

import pytest

from backend.risk.drawdown_monitor import DrawdownMonitor, DrawdownStatus
from backend.risk.kelly_criterion import KellyCriterion
from backend.risk.risk_orchestrator import RiskOrchestrator, TradeSignal


class TestRiskOrchestratorPreTradeCheck:
    """Test Fase C: RiskOrchestrator pre-trade validatie."""

    def test_pre_trade_check_approves_valid_signal(self):
        """Test dat een valide signal wordt goedgekeurd."""
        # Arrange
        risk_orch = RiskOrchestrator()

        signal = TradeSignal(
            symbol="BTC/USD",
            side="long",
            entry_price=50000.0,
            stop_price=49000.0,
            confidence=0.7,
            reward_to_risk=2.0,
            strategy="momentum",
        )

        # Act
        result = risk_orch.pre_trade_check(
            signal=signal,
            portfolio_value=100000.0,
            current_positions_count=2,
        )

        # Assert
        assert result.approved is True
        assert result.reason == "Trade approved"
        assert result.recommended_quantity > 0

    def test_pre_trade_check_rejects_low_confidence(self):
        """Test dat signal met lage confidence wordt afgewezen."""
        # Arrange
        risk_orch = RiskOrchestrator()

        signal = TradeSignal(
            symbol="BTC/USD",
            side="long",
            entry_price=50000.0,
            stop_price=49000.0,
            confidence=0.2,  # Low confidence
            reward_to_risk=2.0,
            strategy="momentum",
        )

        # Act
        result = risk_orch.pre_trade_check(
            signal=signal,
            portfolio_value=100000.0,
            current_positions_count=0,
        )

        # Assert
        assert result.approved is False
        assert "confidence too low" in result.reason

    def test_pre_trade_check_rejects_max_positions(self):
        """Test dat signal wordt afgewezen bij max positions."""
        # Arrange
        risk_orch = RiskOrchestrator(max_positions=5)

        signal = TradeSignal(
            symbol="BTC/USD",
            side="long",
            entry_price=50000.0,
            stop_price=49000.0,
            confidence=0.7,
            reward_to_risk=2.0,
        )

        # Act
        result = risk_orch.pre_trade_check(
            signal=signal,
            portfolio_value=100000.0,
            current_positions_count=5,  # Max reached
        )

        # Assert
        assert result.approved is False
        assert "Max positions limit reached" in result.reason

    def test_pre_trade_check_kill_switch_active(self):
        """Test dat alle trades worden geblokkeerd bij kill switch."""
        # Arrange
        mock_drawdown = MagicMock(spec=DrawdownMonitor)
        mock_drawdown.check.return_value = DrawdownStatus.KILL_SWITCH
        mock_drawdown.get_drawdown_pct.return_value = 0.25

        risk_orch = RiskOrchestrator(drawdown_monitor=mock_drawdown)

        signal = TradeSignal(
            symbol="BTC/USD",
            side="long",
            entry_price=50000.0,
            stop_price=49000.0,
            confidence=0.9,  # High confidence
            reward_to_risk=3.0,
        )

        # Act
        result = risk_orch.pre_trade_check(
            signal=signal,
            portfolio_value=100000.0,
        )

        # Assert
        assert result.approved is False
        assert "KILL SWITCH" in result.reason
        assert result.drawdown_status == DrawdownStatus.KILL_SWITCH

    def test_pre_trade_check_uses_kelly_for_high_confidence(self):
        """Test dat Kelly criterion wordt gebruikt voor hoge confidence."""
        # Arrange
        risk_orch = RiskOrchestrator()

        signal = TradeSignal(
            symbol="BTC/USD",
            side="long",
            entry_price=50000.0,
            stop_price=49000.0,
            confidence=0.6,  # High enough for Kelly
            reward_to_risk=2.0,
        )

        # Act
        result = risk_orch.pre_trade_check(
            signal=signal,
            portfolio_value=100000.0,
        )

        # Assert
        assert result.approved is True
        assert result.sizing_method == "kelly"
        assert result.kelly_fraction is not None

    def test_pre_trade_check_uses_fixed_risk_for_low_confidence(self):
        """Test dat fixed risk wordt gebruikt voor lagere confidence."""
        # Arrange
        risk_orch = RiskOrchestrator()

        signal = TradeSignal(
            symbol="BTC/USD",
            side="long",
            entry_price=50000.0,
            stop_price=49000.0,
            confidence=0.4,  # Low for Kelly, high enough for trade
            reward_to_risk=2.0,
        )

        # Act
        result = risk_orch.pre_trade_check(
            signal=signal,
            portfolio_value=100000.0,
        )

        # Assert
        assert result.approved is True
        assert result.sizing_method == "fixed_risk"


class TestDrawdownMonitorIntegration:
    """Test Fase C: Drawdown monitor integratie."""

    def test_drawdown_monitor_soft_limit_reduces_exposure(self):
        """Test dat soft limit exposure vermindert."""
        # Arrange
        drawdown_monitor = DrawdownMonitor(
            soft_limit=0.15,  # 15% drawdown
            hard_limit=0.25,  # 25% drawdown
        )

        # Simulate drawdown
        for value in [100000, 95000, 90000, 85000]:  # 15% drawdown
            status = drawdown_monitor.check(value)

        # Act - check status at 15% drawdown
        assert status == DrawdownStatus.REDUCE_EXPOSURE

    def test_drawdown_monitor_hard_limit_triggers_kill_switch(self):
        """Test dat hard limit kill switch triggert."""
        # Arrange
        drawdown_monitor = DrawdownMonitor(
            soft_limit=0.15,
            hard_limit=0.25,  # 25% drawdown
        )

        # Simulate severe drawdown
        for value in [100000, 90000, 80000, 75000]:  # 25% drawdown
            status = drawdown_monitor.check(value)

        # Act & Assert
        assert status == DrawdownStatus.KILL_SWITCH

    def test_drawdown_monitor_normal_operation(self):
        """Test normale operatie zonder drawdown."""
        # Arrange
        drawdown_monitor = DrawdownMonitor(
            soft_limit=0.15,
            hard_limit=0.25,
        )

        # Simulate normal values with minor fluctuations
        values = [100000, 101000, 99000, 100500, 99800]

        # Act
        for value in values:
            status = drawdown_monitor.check(value)

        # Assert
        assert status == DrawdownStatus.OK


class TestKellyCriterion:
    """Test Fase C: Kelly Criterion berekeningen."""

    def test_kelly_fraction_calculation(self):
        """Test Kelly fraction berekening."""
        # Arrange
        kelly = KellyCriterion(conservative_factor=0.25)

        # Act
        result = kelly.calculate(
            win_probability=0.6,
            win_loss_ratio=2.0,  # Risk/Reward = 1:2
            portfolio_value=100000.0,
        )

        # Assert
        # Kelly = (0.6 * 2 - 0.4) / 2 = 0.4
        # Conservative = 0.4 * 0.25 = 0.1
        assert result.optimal_fraction == pytest.approx(0.4, rel=0.01)
        assert result.recommended_size == pytest.approx(10000.0, rel=0.01)  # 10% of portfolio

    def test_kelly_recommends_zero_for_unfavorable_odds(self):
        """Test dat Kelly 0 adviseert bij ongunstige odds."""
        # Arrange
        kelly = KellyCriterion()

        # Act - 40% win rate with 1:1 payoff
        result = kelly.calculate(
            win_probability=0.4,
            win_loss_ratio=1.0,
            portfolio_value=100000.0,
        )

        # Assert
        assert result.optimal_fraction <= 0.0


class TestRiskOrchestratorInOODA:
    """Test Fase C: RiskOrchestrator in OODA coordinator."""

    def test_risk_orchestrator_integration_exists(self):
        """Test dat RiskOrchestrator correct wordt geïnitialiseerd in coordinator."""
        from backend.orchestration.ooda_coordinator import OODALoopCoordinator

        # Arrange & Act
        risk_orch = RiskOrchestrator()
        coordinator = OODALoopCoordinator(
            data_scout=MagicMock(),
            analyst=MagicMock(),
            trader=MagicMock(),
            risk_manager=MagicMock(),
            fund_manager=MagicMock(),
            bull_researcher=MagicMock(),
            bear_researcher=MagicMock(),
            cognitive_bridge=MagicMock(),
            risk_orchestrator=risk_orch,
        )

        # Assert
        assert coordinator.risk_orchestrator is risk_orch

    def test_risk_orchestrator_blocks_trade(self):
        """Test dat RiskOrchestrator een trade kan blokkeren."""
        # Arrange
        risk_orch = RiskOrchestrator()

        # Create signal that should be blocked (low confidence)
        signal = TradeSignal(
            symbol="BTC/USD",
            side="buy",
            entry_price=50000.0,
            stop_price=49000.0,
            confidence=0.2,  # Low confidence should be rejected
            reward_to_risk=2.0,
        )

        # Act
        result = risk_orch.pre_trade_check(
            signal=signal,
            portfolio_value=100000.0,
        )

        # Assert
        assert result.approved is False
        assert "confidence too low" in result.reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
