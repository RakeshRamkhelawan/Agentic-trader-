import pytest

from backend.core.risk.guna_sizing import GunaSizer, GunaType
from backend.core.risk.mifid_checks import (
    ClientClassification,
    ClientProfile,
    ComplianceStatus,
    MiFIDGuard,
    TradeRequest,
)
from backend.core.risk.risk_manager import RiskManager


class TestRiskModule:

    def test_mifid_retail_block(self):
        # Scenario: Retail client, low knowledge -> Block
        profile = ClientProfile(
            classification=ClientClassification.RETAIL,
            experience_years=0,
            knowledge_score=3,
            max_loss_tolerance_pct=10.0,
            current_drawdown_pct=0.0,
        )
        trade = TradeRequest(
            asset="BTC", amount=1.0, price=50000.0, side="buy", notional_value=50000.0
        )

        guard = MiFIDGuard()
        status = guard.validate(profile, trade)
        assert status == ComplianceStatus.BLOCK

    def test_mifid_drawdown_block(self):
        # Scenario: Professional client (passes suitability) but Drawdown > Limit -> Block
        profile = ClientProfile(
            classification=ClientClassification.PROFESSIONAL,
            experience_years=5,
            knowledge_score=9,
            max_loss_tolerance_pct=10.0,
            current_drawdown_pct=11.0,  # Exceeded
        )
        trade = TradeRequest(
            asset="BTC", amount=1.0, price=50000.0, side="buy", notional_value=50000.0
        )

        guard = MiFIDGuard()
        status = guard.validate(profile, trade)
        assert status == ComplianceStatus.BLOCK

    def test_guna_sizing(self):
        sizer = GunaSizer()

        assert sizer.calculate_size_multiplier(GunaType.SATTVA) == 1.0
        assert sizer.calculate_size_multiplier(GunaType.RAJAS) == 1.2
        assert sizer.calculate_size_multiplier(GunaType.TAMAS) == 0.5

    def test_risk_manager_aggregation(self):
        # Scenario: Professional Client, Healthy Drawdown, Tamas State -> Reduce Size
        profile = ClientProfile(
            classification=ClientClassification.PROFESSIONAL,
            experience_years=5,
            knowledge_score=9,
            max_loss_tolerance_pct=10.0,
            current_drawdown_pct=0.0,
        )
        trade = TradeRequest(
            asset="BTC", amount=1.0, price=50000.0, side="buy", notional_value=50000.0
        )

        manager = RiskManager()
        decision = manager.evaluate_trade(profile, trade, GunaType.TAMAS)

        assert decision.decision == "accept"
        assert decision.adjusted_size == 0.5  # 1.0 * 0.5
        assert "tamas" in decision.reason
