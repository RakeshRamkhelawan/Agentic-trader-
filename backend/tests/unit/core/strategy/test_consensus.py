"""
Tests voor TradingConsensusEngine.
"""

from backend.core.strategy.consensus import TradingConsensusEngine, Vote


class TestTradingConsensusEngine:

    def test_empty_votes_is_rejected(self):
        engine = TradingConsensusEngine()
        result = engine.evaluate_proposal([])
        assert result["approved"] is False
        assert result["score"] == 0.0

    def test_strong_approval_all_providers(self):
        engine = TradingConsensusEngine(approval_threshold=0.5)
        votes: list[Vote] = [
            {"provider": "technical_strategy", "score": 1.0, "reasoning": "Strong trend"},
            {"provider": "mtf_analyzer", "score": 1.0, "reasoning": "Macro aligned"},
            {"provider": "risk_manager", "score": 1.0, "reasoning": "Risk OK"},
        ]
        
        result = engine.evaluate_proposal(votes)
        assert result["approved"] is True
        assert result["score"] == 1.0
        assert "APPROVED" in result["reasoning"]

    def test_veto_rejects_despite_good_average(self):
        engine = TradingConsensusEngine(approval_threshold=0.2)
        # Even with high scores from tech and MTF, Risk Manager veto drops approval
        votes: list[Vote] = [
            {"provider": "technical_strategy", "score": 1.0, "reasoning": "Strong setup"},
            {"provider": "mtf_analyzer", "score": 1.0, "reasoning": "Macro bullish"},
            {"provider": "risk_manager", "score": -0.9, "reasoning": "VETO: Exposure too high"},
        ]
        
        result = engine.evaluate_proposal(votes)
        assert result["approved"] is False
        assert "VETO by risk_manager" in result["reasoning"]

    def test_missed_provider_weight_normalization(self):
        engine = TradingConsensusEngine(approval_threshold=0.4)
        # Only technical votes (weight 0.40)
        votes: list[Vote] = [
            {"provider": "technical_strategy", "score": 0.8, "reasoning": "Good setup"},
        ]
        
        result = engine.evaluate_proposal(votes)
        # Normalized score should be (0.8 * 0.40) / 0.40 = 0.8
        assert result["approved"] is True
        assert result["score"] == 0.8

    def test_mixed_signals_below_threshold(self):
        engine = TradingConsensusEngine(approval_threshold=0.5)
        # Mixed signals that don't reach 0.5 threshold
        votes: list[Vote] = [
            {"provider": "technical_strategy", "score": 0.6, "reasoning": "Ok setup"}, # 0.6 * 0.4 = 0.24
            {"provider": "mtf_analyzer", "score": -0.1, "reasoning": "Slight macro headwind"}, # -0.1 * 0.3 = -0.03
            {"provider": "risk_manager", "score": 0.5, "reasoning": "Risk fine"}, # 0.5 * 0.3 = 0.15
        ]
        # Total score: 0.24 - 0.03 + 0.15 = 0.36
        # Applied weight: 0.4 + 0.3 + 0.3 = 1.0
        # Final: 0.36
        result = engine.evaluate_proposal(votes)
        assert result["approved"] is False
        assert result["score"] == 0.36
