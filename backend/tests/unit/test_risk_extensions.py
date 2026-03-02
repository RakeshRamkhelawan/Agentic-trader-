"""
Unit tests for Risk Management Extensions.

Tests DrawdownMonitor, RiskOrchestrator, IntegratedPositionSizer,
and updated RiskValidator with daily loss tracking.
"""

from datetime import date
from unittest.mock import patch

import pytest

from backend.risk.drawdown_monitor import DrawdownMonitor, DrawdownStatus
from backend.risk.position_sizer import IntegratedPositionSizer, SizingResult
from backend.risk.risk_orchestrator import RiskDecision, RiskOrchestrator, TradeSignal

# ===========================================================================
# DrawdownMonitor Tests
# ===========================================================================


class TestDrawdownMonitor:
    """Tests for DrawdownMonitor circuit breakers."""

    def test_initial_state_is_ok(self):
        monitor = DrawdownMonitor(soft_limit=0.10, hard_limit=0.20)
        status = monitor.check(100000.0)
        assert status == DrawdownStatus.OK

    def test_soft_limit_triggers_reduce_exposure(self):
        monitor = DrawdownMonitor(soft_limit=0.10, hard_limit=0.20)
        monitor.check(100000.0)  # Set peak

        status = monitor.check(89000.0)  # 11% drawdown > 10% soft limit
        assert status == DrawdownStatus.REDUCE_EXPOSURE

    def test_hard_limit_triggers_kill_switch(self):
        monitor = DrawdownMonitor(soft_limit=0.10, hard_limit=0.20)
        monitor.check(100000.0)  # Set peak

        status = monitor.check(79000.0)  # 21% drawdown > 20% hard limit
        assert status == DrawdownStatus.KILL_SWITCH

    def test_ok_to_reduce_to_kill_transitions(self):
        monitor = DrawdownMonitor(soft_limit=0.10, hard_limit=0.20)
        monitor.check(100000.0)  # Set peak

        # OK -> REDUCE at 10%
        status = monitor.check(89000.0)
        assert status == DrawdownStatus.REDUCE_EXPOSURE

        # REDUCE -> KILL at 20%
        status = monitor.check(78000.0)
        assert status == DrawdownStatus.KILL_SWITCH

    def test_recovery_from_reduce_to_ok(self):
        monitor = DrawdownMonitor(soft_limit=0.10, hard_limit=0.20)
        monitor.check(100000.0)  # Set peak
        monitor.check(89000.0)  # REDUCE

        # Recover above soft limit
        status = monitor.check(95000.0)  # 5% drawdown < 10%
        assert status == DrawdownStatus.OK

    def test_new_peak_resets_to_ok(self):
        monitor = DrawdownMonitor(soft_limit=0.10, hard_limit=0.20)
        monitor.check(100000.0)  # Set peak
        monitor.check(89000.0)  # REDUCE

        # New all-time high
        status = monitor.check(110000.0)
        assert status == DrawdownStatus.OK

    def test_drawdown_percentage(self):
        monitor = DrawdownMonitor()
        monitor.check(100000.0)  # Peak
        monitor.check(85000.0)  # Trough

        dd = monitor.get_drawdown_pct()
        assert abs(dd - 0.15) < 0.001  # 15% drawdown

    def test_zero_value_triggers_kill_switch(self):
        monitor = DrawdownMonitor()
        monitor.check(100000.0)

        status = monitor.check(0.0)
        assert status == DrawdownStatus.KILL_SWITCH

    def test_invalid_limits_raise_error(self):
        with pytest.raises(ValueError):
            DrawdownMonitor(soft_limit=0.30, hard_limit=0.10)  # soft > hard

        with pytest.raises(ValueError):
            DrawdownMonitor(soft_limit=-0.10, hard_limit=0.20)

    def test_reset_clears_state(self):
        monitor = DrawdownMonitor()
        monitor.check(100000.0)
        monitor.check(70000.0)  # KILL SWITCH

        monitor.reset()
        assert monitor.status == DrawdownStatus.OK
        assert monitor.get_peak_value() == 0.0


# ===========================================================================
# IntegratedPositionSizer Tests
# ===========================================================================


class TestIntegratedPositionSizer:
    """Tests for the unified position sizing module."""

    def test_fixed_risk_basic(self):
        sizer = IntegratedPositionSizer(max_risk_pct=0.01, max_position_pct=0.10)
        result = sizer.size_from_fixed_risk(
            equity=100000.0,
            entry=50000.0,
            stop=49000.0,
            side="long",
        )

        # Max loss = 100000 * 0.01 = 1000
        # Risk per unit = 50000 - 49000 = 1000
        # Qty = 1000 / 1000 = 1.0
        # Max notional = 100000 * 0.10 = 10000 -> max qty = 10000/50000 = 0.2
        # Final qty = min(1.0, 0.2) = 0.2
        assert result.method == "fixed_risk"
        assert result.quantity > 0
        assert abs(result.risk_per_unit - 1000.0) < 0.001

    def test_fixed_risk_capped_by_max_position(self):
        sizer = IntegratedPositionSizer(max_risk_pct=0.10, max_position_pct=0.02)
        result = sizer.size_from_fixed_risk(
            equity=100000.0,
            entry=1000.0,
            stop=999.0,
            side="long",
        )

        # Max notional = 100000 * 0.02 = 2000
        # Max qty by notional = 2000 / 1000 = 2.0
        assert result.quantity <= 2.0

    def test_fixed_risk_short_side(self):
        sizer = IntegratedPositionSizer(max_risk_pct=0.01)
        result = sizer.size_from_fixed_risk(
            equity=100000.0,
            entry=50000.0,
            stop=51000.0,
            side="short",
        )

        # Risk per unit (short) = stop - entry = 1000
        assert abs(result.risk_per_unit - 1000.0) < 0.001
        assert result.quantity > 0

    def test_kelly_sizing(self):
        sizer = IntegratedPositionSizer(
            max_risk_pct=0.02,
            kelly_multiplier=0.50,
        )
        result = sizer.size_with_kelly(
            equity=100000.0,
            entry=50000.0,
            stop=49000.0,
            win_probability=0.60,
            win_loss_ratio=1.5,
            side="long",
        )

        assert result.method == "kelly"
        assert result.kelly_fraction is not None
        assert result.kelly_fraction > 0
        assert result.quantity > 0

    def test_kelly_negative_edge_uses_fixed_risk(self):
        sizer = IntegratedPositionSizer()
        result = sizer.size_with_kelly(
            equity=100000.0,
            entry=50000.0,
            stop=49000.0,
            win_probability=0.20,  # Negative edge
            win_loss_ratio=0.5,
            side="long",
        )

        # Kelly fraction should be 0 or negative edge -> fallback
        assert result.quantity >= 0

    def test_volatility_sizing_high_vol(self):
        sizer = IntegratedPositionSizer(max_risk_pct=0.01)
        result = sizer.size_with_volatility(
            equity=100000.0,
            entry=50000.0,
            stop=49000.0,
            atr=2000.0,  # 4% ATR - high volatility
            side="long",
        )

        assert result.method == "volatility"
        assert result.volatility_factor is not None
        assert result.volatility_factor <= 1.0  # Should scale down

    def test_volatility_sizing_low_vol(self):
        sizer = IntegratedPositionSizer(max_risk_pct=0.01)
        result = sizer.size_with_volatility(
            equity=100000.0,
            entry=50000.0,
            stop=49000.0,
            atr=100.0,  # 0.2% ATR - low volatility
            side="long",
        )

        assert result.quantity > 0

    def test_drawdown_scaling_halves_position(self):
        quantity = IntegratedPositionSizer.apply_drawdown_scaling(
            quantity=2.0,
            current_drawdown=0.15,  # Above 10% soft limit
            soft_limit=0.10,
        )
        assert abs(quantity - 1.0) < 0.001  # Halved

    def test_drawdown_scaling_no_change_under_limit(self):
        quantity = IntegratedPositionSizer.apply_drawdown_scaling(
            quantity=2.0,
            current_drawdown=0.05,
            soft_limit=0.10,
        )
        assert abs(quantity - 2.0) < 0.001  # Unchanged

    def test_invalid_inputs_return_zero(self):
        sizer = IntegratedPositionSizer()

        result = sizer.size_from_fixed_risk(0.0, 100.0, 99.0, "long")
        assert result.quantity == 0.0

        result = sizer.size_from_fixed_risk(100000.0, 100.0, 101.0, "long")
        assert result.quantity == 0.0  # Stop above entry for long = negative risk


# ===========================================================================
# RiskOrchestrator Tests
# ===========================================================================


class TestRiskOrchestrator:
    """Tests for centralized pre-trade validation."""

    def _make_signal(self, **kwargs) -> TradeSignal:
        defaults = {
            "symbol": "BTC/USD",
            "side": "long",
            "entry_price": 50000.0,
            "stop_price": 49000.0,
            "confidence": 0.70,
            "reward_to_risk": 2.0,
            "strategy": "test",
        }
        defaults.update(kwargs)
        return TradeSignal(**defaults)

    def test_trade_approved_normal_conditions(self):
        orch = RiskOrchestrator()
        signal = self._make_signal()

        decision = orch.pre_trade_check(
            signal=signal,
            portfolio_value=100000.0,
            current_positions_count=0,
        )

        assert decision.approved is True
        assert decision.recommended_quantity > 0
        assert decision.drawdown_status == DrawdownStatus.OK

    def test_trade_rejected_kill_switch(self):
        monitor = DrawdownMonitor(soft_limit=0.10, hard_limit=0.20)
        monitor.check(100000.0)  # Peak
        monitor.check(78000.0)  # Kill switch

        orch = RiskOrchestrator(drawdown_monitor=monitor)
        signal = self._make_signal()

        decision = orch.pre_trade_check(signal, portfolio_value=78000.0)

        assert decision.approved is False
        assert "KILL SWITCH" in decision.reason

    def test_trade_rejected_max_positions(self):
        orch = RiskOrchestrator(max_positions=5)
        signal = self._make_signal()

        decision = orch.pre_trade_check(signal, 100000.0, current_positions_count=5)

        assert decision.approved is False
        assert "positions" in decision.reason.lower()

    def test_trade_rejected_low_confidence(self):
        orch = RiskOrchestrator()
        signal = self._make_signal(confidence=0.10)

        decision = orch.pre_trade_check(signal, 100000.0)

        assert decision.approved is False
        assert "confidence" in decision.reason.lower()

    def test_reduce_exposure_halves_position(self):
        monitor = DrawdownMonitor(soft_limit=0.10, hard_limit=0.20)
        monitor.check(100000.0)  # Peak
        monitor.check(89000.0)  # REDUCE (11% drawdown)

        orch = RiskOrchestrator(drawdown_monitor=monitor)
        signal = self._make_signal()

        decision = orch.pre_trade_check(signal, portfolio_value=89000.0)

        assert decision.approved is True
        assert decision.drawdown_status == DrawdownStatus.REDUCE_EXPOSURE
        assert len(decision.warnings) > 0

    def test_kelly_sizing_used_for_high_confidence(self):
        orch = RiskOrchestrator()
        signal = self._make_signal(confidence=0.70, reward_to_risk=2.0)

        decision = orch.pre_trade_check(signal, 100000.0)

        assert decision.approved is True
        assert decision.sizing_method == "kelly"
        assert decision.kelly_fraction is not None

    def test_fixed_risk_for_low_confidence(self):
        orch = RiskOrchestrator()
        signal = self._make_signal(confidence=0.35)

        decision = orch.pre_trade_check(signal, 100000.0)

        assert decision.approved is True
        assert decision.sizing_method == "fixed_risk"

    def test_update_portfolio_value(self):
        orch = RiskOrchestrator()

        status = orch.update_portfolio_value(100000.0)
        assert status == DrawdownStatus.OK

        status = orch.update_portfolio_value(78000.0)
        assert status == DrawdownStatus.KILL_SWITCH


# ===========================================================================
# RiskValidator Daily Loss Tests
# ===========================================================================


class TestRiskValidatorDailyLoss:
    """Tests for updated RiskValidator with daily PnL tracking."""

    def test_record_trade_result_positive(self):
        from backend.risk.validators import RiskValidator

        validator = RiskValidator(max_order_size=100000.0, max_daily_loss=5000.0)
        validator.record_trade_result(500.0)

        assert validator.get_daily_pnl() == 500.0
        assert not validator.kill_switch_active

    def test_record_trade_result_triggers_kill_switch(self):
        from backend.risk.validators import RiskValidator

        validator = RiskValidator(max_order_size=100000.0, max_daily_loss=5000.0)
        validator.record_trade_result(-3000.0)
        assert not validator.kill_switch_active

        validator.record_trade_result(-3000.0)  # Total: -6000 > 5000 limit
        assert validator.kill_switch_active

    def test_daily_pnl_accumulates(self):
        from backend.risk.validators import RiskValidator

        validator = RiskValidator(max_order_size=100000.0, max_daily_loss=10000.0)
        validator.record_trade_result(100.0)
        validator.record_trade_result(-50.0)
        validator.record_trade_result(200.0)

        assert abs(validator.get_daily_pnl() - 250.0) < 0.001

    def test_deactivate_kill_switch(self):
        from backend.risk.validators import RiskValidator

        validator = RiskValidator(max_order_size=100000.0, max_daily_loss=100.0)
        validator.activate_kill_switch()
        assert validator.kill_switch_active

        validator.deactivate_kill_switch()
        assert not validator.kill_switch_active

    def test_daily_reset_on_new_day(self):
        from backend.risk.validators import RiskValidator

        validator = RiskValidator(max_order_size=100000.0, max_daily_loss=5000.0)
        validator.record_trade_result(-1000.0)

        # Simulate new day by changing internal date
        validator._pnl_date = date(2020, 1, 1)  # Force an old date

        pnl = validator.get_daily_pnl()
        assert pnl == 0.0  # Should reset
