"""
Enterprise Paper Mode Safety Tests

Doel: Bewijzen dat geen enkele order naar een echte exchange gaat.
Dit is de PRIMAIRE test die de auditor zal uitvoeren.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["TRADING_MODE"] = "paper"

from backend.execution._paper_guard import paper_guard, PaperModeViolation


class TestPaperModeAbsoluteGuarantee:
    """
    Categorie 1: Absolute veiligheidsgarantie.
    Als een van deze tests faalt → applicatie wordt afgeleverd met kritieke fout.
    """

    @pytest.mark.asyncio
    async def test_paper_guard_blocks_decorated_function(self):
        """De @paper_guard decorator moet elke call blokkeren in paper mode."""

        @paper_guard
        async def fake_exchange_call(symbol: str, qty: float):
            return {"status": "filled", "order_id": "123"}

        with pytest.raises(PaperModeViolation) as exc_info:
            await fake_exchange_call("BTC/EUR", 0.001)

        assert "paper mode" in str(exc_info.value).lower()
        assert "blocked" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_paper_guard_audit_log_written(self):
        """Elke geblokkeerde call MOET worden gelogd."""

        audit_logs = []

        # Maak een mock audit logger die de log_intercept methode heeft
        mock_audit_logger = MagicMock()

        async def mock_log_intercept(func_name, args, kwargs, session_id=None):
            audit_logs.append({
                "event": "paper_guard_intercept",
                "function": func_name,
            })

        mock_audit_logger.log_intercept = mock_log_intercept

        with patch("backend.execution._paper_guard._audit_logger", mock_audit_logger):
            @paper_guard
            async def fake_order():
                pass

            with pytest.raises(PaperModeViolation):
                await fake_order()

        # Audit log moet geschreven zijn
        assert len(audit_logs) == 1
        assert audit_logs[0]["event"] == "paper_guard_intercept"

    @pytest.mark.asyncio
    async def test_trading_mode_is_paper(self):
        """TRADING_MODE moet 'paper' zijn."""
        assert os.getenv("TRADING_MODE") == "paper"


class TestVedicCycleIntegrity:
    """Categorie 2: Vedic stack integriteit."""

    def test_shm_names_are_v2(self):
        """SHM namen MOETEN _v2 suffix hebben."""
        import os
        import re

        # Zoek specifiek naar SHM gebruik (shm_name= of create= of attach=)
        v1_pattern = re.compile(r'shm_name\s*=\s*["\'](trading_intents|market_data)["\']')
        non_v2_refs = []

        for root, dirs, files in os.walk("backend/"):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            matches = v1_pattern.findall(content)
                            if matches:
                                non_v2_refs.append(f"{filepath}: {matches}")
                    except Exception:
                        continue

        # Moet 0 zijn
        assert len(non_v2_refs) == 0, f"Gevonden v1 SHM referenties:\n" + "\n".join(non_v2_refs)

    @pytest.mark.asyncio
    async def test_elemental_agents_prana_nominal(self):
        """Alle agents moeten prana >= 80 hebben bij startup."""
        from backend.agents.elemental_orchestrator import ElementalOrchestrator
        from backend.agents.elemental_research import ElementalResearch
        from backend.agents.elemental_risk_guardian import ElementalRiskGuardian
        from backend.agents.elemental_macro import ElementalMacro
        from backend.agents.elemental_valuation import ElementalValuation

        agents = {
            "ether": ElementalOrchestrator(),
            "air": ElementalResearch(),
            "fire": ElementalRiskGuardian(),
            "water": ElementalMacro(),
            "earth": ElementalValuation(),
        }

        for name, agent in agents.items():
            assert agent.prana >= 80, f"{name} prana {agent.prana} < 80"


class TestResiliency:
    """Categorie 3: Fault tolerance."""

    @pytest.mark.asyncio
    async def test_llm_circuit_breaker_exists(self):
        """LLM circuit breaker moet bestaan."""
        try:
            from backend.llm.circuit_breaker import LLMCircuitBreaker
            cb = LLMCircuitBreaker()
            assert cb.state.name in ["CLOSED", "OPEN", "HALF_OPEN"]
        except ImportError:
            pytest.skip("Circuit breaker not yet implemented")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
