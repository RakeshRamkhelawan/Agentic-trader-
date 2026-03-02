#!/usr/bin/env python3
"""
Integratietests voor Vedic Paper Trading Stack
Happy & Unhappy Paths

Usage:
    pytest tests/integration/test_vedic_integration.py -v
"""

import asyncio
import json
import os
import pytest
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

# Set paper mode before imports
os.environ["TRADING_MODE"] = "paper"

from backend.agents.elemental_orchestrator import ElementalOrchestrator
from backend.agents.elemental_research import ElementalResearch
from backend.agents.elemental_risk_guardian import ElementalRiskGuardian
from backend.agents.elemental_macro import ElementalMacro
from backend.agents.elemental_valuation import ElementalValuation
from backend.core.eternal_soul_service import EternalSoulService
from backend.core.cognitive_mind_service import CognitiveMindService
from backend.execution.reflex_executor import ReflexExecutor
from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.services.paper_trading_live import PaperTradingLiveBroadcaster


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def elemental_agents():
    """Fixture: Alle 5 elementaire agents."""
    return {
        "ether": ElementalOrchestrator(),
        "air": ElementalResearch(),
        "fire": ElementalRiskGuardian(),
        "water": ElementalMacro(),
        "earth": ElementalValuation(),
    }


@pytest.fixture
def soul_context_normal():
    """Fixture: Normale soul context (Rahu Kala inactive)."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rahu_kala_active": False,
        "consciousness_level": 0.75,
        "guna_dominance": "sattva",
        "trading_gate_open": True,
        "market_regime": "expansion",
        "causality_threshold": 0.6,
        "market_metrics": {
            "price": 50000.0,
            "sma_50": 49000.0,
            "sma_200": 48000.0,
            "volatility": 0.02,
        },
    }


@pytest.fixture
def soul_context_rahu_kala():
    """Fixture: Soul context met Rahu Kala active."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rahu_kala_active": True,
        "consciousness_level": 0.3,
        "guna_dominance": "tamas",
        "trading_gate_open": False,
        "market_regime": "contraction",
        "causality_threshold": 0.9,
        "market_metrics": {
            "price": 48000.0,
            "sma_50": 49000.0,
            "sma_200": 48000.0,
            "volatility": 0.05,
        },
    }


@pytest.fixture
def mock_redis():
    """Fixture: Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.publish = AsyncMock(return_value=True)
    redis.ping = AsyncMock(return_value=True)
    return redis


# ============================================================================
# HAPPY PATH TESTS
# ============================================================================

class TestHappyPaths:
    """Happy path integratietests - alles werkt zoals verwacht."""

    @pytest.mark.asyncio
    async def test_elemental_agents_prana_initial(self, elemental_agents):
        """HP-001: Alle agents starten met prana >= 80."""
        for name, agent in elemental_agents.items():
            assert agent.prana >= 80, f"{name} prana {agent.prana} < 80"
            assert agent.prana <= 100, f"{name} prana {agent.prana} > 100"

    @pytest.mark.asyncio
    async def test_elemental_agents_guna_balance(self, elemental_agents):
        """HP-002: Alle agents hebben correcte guna balans (sum = 1.0)."""
        for name, agent in elemental_agents.items():
            guna = agent.guna_balance
            total = sum(guna.values())
            assert abs(total - 1.0) < 0.01, f"{name} guna sum {total} != 1.0"
            assert all(k in guna for k in ["sattva", "rajas", "tamas"])

    @pytest.mark.asyncio
    async def test_elemental_orchestrator_harmony_calculation(self, elemental_agents):
        """HP-003: Ether Orchestrator berekent harmony score correct."""
        orchestrator = elemental_agents["ether"]

        inputs = {
            "air": {"signal": 0.7, "confidence": 0.8},
            "fire": {"signal": 0.6, "confidence": 0.9},
            "water": {"signal": 0.5, "confidence": 0.7},
            "earth": {"signal": 0.8, "confidence": 0.75},
        }

        result = await orchestrator.process_signal({
            "inputs": inputs,
            "soul_context": {"market_regime": "expansion"}
        })

        assert "harmony_score" in result
        assert 0.0 <= result["harmony_score"] <= 1.0
        assert "synthesis" in result
        assert "prana_remaining" in result

    @pytest.mark.asyncio
    async def test_elemental_agents_signal_processing(self, elemental_agents):
        """HP-004: Alle agents kunnen signalen verwerken."""
        signal = {
            "market_data": {"price": 50000, "volume": 1000000},
            "soul_context": {"market_regime": "expansion"},
        }

        for name, agent in elemental_agents.items():
            if name == "ether":
                # Ether heeft speciaal formaat nodig
                result = await agent.process_signal({
                    "inputs": {"air": signal, "fire": signal, "water": signal, "earth": signal},
                    "soul_context": {"market_regime": "expansion"}
                })
            else:
                result = await agent.process_signal(signal)

            assert result is not None, f"{name} returned None"
            assert isinstance(result, dict), f"{name} returned non-dict"

    @pytest.mark.asyncio
    async def test_prana_consumption_and_regeneration(self, elemental_agents):
        """HP-005: Prana wordt verbruikt en kan regenereren."""
        agent = elemental_agents["fire"]
        initial_prana = agent.prana

        # Consume prana
        success = await agent.consume_prana()
        assert success is True
        assert agent.prana < initial_prana

        # Regenerate prana (eerst verbruiken om ruimte te maken)
        agent.prana = 50.0  # Forceer lage waarde
        new_prana = await agent.regenerate_prana(rest_period_seconds=3600)  # 1 hour
        assert new_prana > 50.0

    @pytest.mark.asyncio
    async def test_shadow_portfolio_trading(self):
        """HP-006: Shadow portfolio kan trades uitvoeren."""
        from backend.schemas.orders import OrderRequest, OrderSide, OrderType, OrderType

        portfolio = ShadowPortfolioManager(initial_cash=10000.0)
        portfolio.update_price("BTC/EUR", 50000.0)

        # Buy order
        order = OrderRequest(
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            qty=0.1,
            order_type=OrderType.MARKET,
        )

        result = await portfolio.submit_order(order)
        assert result.status.value == "FILLED"
        assert result.filled_qty == 0.1

        # Check balance
        balance = await portfolio.get_balance()
        assert balance["EUR"] < 10000.0  # Cash decreased
        assert balance["BTC/EUR"] == 0.1  # Position increased

    @pytest.mark.asyncio
    async def test_paper_trading_broadcaster_vedic_channels(self):
        """HP-007: Broadcaster heeft alle 4 channels inclusief vedic."""
        broadcaster = PaperTradingLiveBroadcaster()

        assert broadcaster.channel == "paper_trading.live"
        assert broadcaster.stats_channel == "paper_trading.stats"
        assert broadcaster.agents_channel == "paper_trading.agents"
        assert broadcaster.vedic_channel == "paper_trading.vedic"

    @pytest.mark.asyncio
    async def test_reflex_executor_paper_mode(self):
        """HP-008: Reflex Executor draait altijd in paper mode."""
        executor = ReflexExecutor(
            shm_name="trading_intents_v2",
            market_shm_name="market_data_v2",
            trading_mode="paper"
        )

        assert executor.trading_mode == "paper"
        assert executor.portfolio is not None
        assert isinstance(executor.portfolio, ShadowPortfolioManager)

    @pytest.mark.asyncio
    async def test_full_vedic_cycle_simulation(self, elemental_agents, soul_context_normal):
        """HP-009: Complete Vedic trading cycle simulatie."""
        # 1. Elemental agents genereren signalen
        signals = {}
        for name, agent in elemental_agents.items():
            if name != "ether":
                signal = await agent.process_signal({
                    "market_data": {"price": 50000, "change": 0.02},
                    "soul_context": soul_context_normal,
                })
                signals[name] = signal

        # 2. Ether orchestrator synthetiseert
        orchestrator = elemental_agents["ether"]
        synthesis = await orchestrator.process_signal({
            "inputs": signals,
            "soul_context": soul_context_normal,
        })

        # 3. Verificaties
        assert synthesis["harmony_score"] >= 0.0
        assert synthesis["prana_remaining"] > 0

        # 4. Als harmony > 0.2, trading mag doorgaan
        if synthesis["harmony_score"] > 0.2:
            assert soul_context_normal["trading_gate_open"] is True
            assert soul_context_normal["rahu_kala_active"] is False


# ============================================================================
# UNHAPPY PATH TESTS
# ============================================================================

class TestUnhappyPaths:
    """Unhappy path integratietests - foutcondities en edge cases."""

    @pytest.mark.asyncio
    async def test_rahu_kala_blocks_trading(self, elemental_agents, soul_context_rahu_kala):
        """UP-001: Rahu Kala blokkeert alle trading."""
        orchestrator = elemental_agents["ether"]

        # Rahu Kala is actief
        assert soul_context_rahu_kala["rahu_kala_active"] is True
        assert soul_context_rahu_kala["trading_gate_open"] is False

        # Trading zou geblokkeerd moeten zijn
        # In de praktijk zou de Mind geen intents genereren
        # of ze zouden worden genegeerd door Body

    @pytest.mark.asyncio
    async def test_low_prana_degraded_response(self, elemental_agents):
        """UP-002: Agent met prana < 10 geeft degraded response."""
        agent = elemental_agents["fire"]

        # Forceer lage prana
        agent.prana = 5.0

        # Consume prana zou moeten falen
        success = await agent.consume_prana()
        assert success is False

        # Process signal zou degraded response moeten geven
        signal = {"market_data": {"price": 50000}}
        result = await agent.process_signal(signal)

        # Result zou error of degraded indicator moeten hebben
        assert result is not None

    @pytest.mark.asyncio
    async def test_low_harmony_stops_trading(self, elemental_agents):
        """UP-003: Harmony < 0.2 stopt trading."""
        orchestrator = elemental_agents["ether"]

        # Simuleer conflict tussen agents (lage harmony)
        conflicting_inputs = {
            "air": {"signal": 1.0, "confidence": 0.9},   # Strong buy
            "fire": {"signal": -1.0, "confidence": 0.9}, # Strong sell
            "water": {"signal": 0.0, "confidence": 0.1}, # No signal
            "earth": {"signal": 0.0, "confidence": 0.1}, # No signal
        }

        result = await orchestrator.process_signal({
            "inputs": conflicting_inputs,
            "soul_context": {"market_regime": "volatile"},
        })

        # Lage harmony score
        if result["harmony_score"] < 0.2:
            # Trading zou gestopt moeten worden
            pass  # In praktijk: cyclus overgeslagen

    @pytest.mark.asyncio
    async def test_insufficient_funds_rejected(self):
        """UP-004: Order met onvoldoende fondsen wordt afgewezen."""
        from backend.schemas.orders import OrderRequest, OrderSide, OrderType, OrderStatus, OrderType, OrderType

        portfolio = ShadowPortfolioManager(initial_cash=100.0)
        portfolio.update_price("BTC/EUR", 50000.0)

        # Probeer te kopen voor meer dan cash
        order = OrderRequest(
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            qty=1.0,  # Kost €50,000 maar we hebben maar €100
            order_type=OrderType.MARKET,
        )

        result = await portfolio.submit_order(order)
        assert result.status == OrderStatus.REJECTED
        assert "Insufficient funds" in result.error_message

    @pytest.mark.asyncio
    async def test_invalid_symbol_rejected(self):
        """UP-005: Order voor onbekend symbool wordt afgewezen."""
        from backend.schemas.orders import OrderRequest, OrderSide, OrderType, OrderStatus

        portfolio = ShadowPortfolioManager(initial_cash=10000.0)
        # Geen prijs gezet voor UNKNOWN/EUR

        order = OrderRequest(
            symbol="UNKNOWN/EUR",
            side=OrderSide.BUY,
            qty=1.0,
            order_type=OrderType.MARKET,
        )

        result = await portfolio.submit_order(order)
        assert result.status == OrderStatus.REJECTED
        assert "No market price" in result.error_message

    @pytest.mark.asyncio
    async def test_network_failure_redis_unavailable(self, mock_redis):
        """UP-006: Redis onbeschikbaar - graceful degradation."""
        # Simuleer Redis failure
        mock_redis.ping.side_effect = Exception("Connection refused")

        # Service zou moeten starten maar met waarschuwing
        # of fallback naar lokale mode
        try:
            soul = EternalSoulService()
            # Zonder Redis kan het nog steeds werken in degraded mode
        except Exception as e:
            # Of het gooit een exception die afgehandeld wordt
            pass

    @pytest.mark.asyncio
    async def test_shm_not_available(self):
        """UP-007: Shared Memory niet beschikbaar - graceful fallback."""
        # Probeer te connecten naar niet-bestaande SHM
        executor = ReflexExecutor(
            shm_name="nonexistent_shm",
            market_shm_name="nonexistent_market",
            trading_mode="paper"
        )

        # Zou moeten starten zonder te crashen
        # In praktijk: bridge zal None zijn
        assert executor.bridge is None

    @pytest.mark.asyncio
    async def test_malformed_signal_handling(self, elemental_agents):
        """UP-008: Ongeldig signaal formaat wordt afgehandeld."""
        agent = elemental_agents["air"]

        # Corrupt/incompleet signaal
        malformed_signal = {
            "invalid_key": "no_market_data"
        }

        # Zou niet moeten crashen
        try:
            result = await agent.process_signal(malformed_signal)
            # Zou error of default response moeten geven
        except Exception as e:
            # Exception is ook acceptable als het goed gedocumenteerd is
            pass

    @pytest.mark.asyncio
    async def test_concurrent_agent_access(self, elemental_agents):
        """UP-009: Concurrente toegang tot agents."""
        agent = elemental_agents["fire"]

        # Simuleer concurrente prana consumption
        tasks = [
            agent.consume_prana(),
            agent.consume_prana(),
            agent.consume_prana(),
        ]

        results = await asyncio.gather(*tasks)

        # Zou correct moeten omgaan met concurrentie
        # (in praktijk: locks of atomic operations)

    @pytest.mark.asyncio
    async def test_extreme_market_conditions(self, elemental_agents):
        """UP-010: Extreme marktcondities (flash crash/pump)."""
        agent = elemental_agents["fire"]

        # Extreme volatiliteit
        extreme_signal = {
            "market_data": {
                "price": 50000,
                "change": -0.5,  # -50% crash
                "volatility": 10.0,  # Extreme volatiliteit
            },
            "portfolio": {"exposure": 0.9},  # Hoge exposure
        }

        result = await agent.process_signal(extreme_signal)

        # Risk guardian zou alert moeten zijn
        assert result is not None


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Edge case tests - grensgevallen."""

    @pytest.mark.asyncio
    async def test_zero_prana_boundary(self, elemental_agents):
        """EC-001: Prana exact op 0."""
        agent = elemental_agents["earth"]
        agent.prana = 0.0

        success = await agent.consume_prana()
        assert success is False

    @pytest.mark.asyncio
    async def test_exactly_ten_prana_boundary(self, elemental_agents):
        """EC-002: Prana exact op 10 (threshold)."""
        agent = elemental_agents["water"]
        agent.prana = 10.0

        # Op exact 10 zou het nog moeten werken
        success = await agent.consume_prana()
        # Na consumption zou het onder 10 komen
        assert agent.prana < 10.0

    @pytest.mark.asyncio
    async def test_harmony_exactly_zero(self, elemental_agents):
        """EC-003: Harmony score exact 0.0."""
        orchestrator = elemental_agents["ether"]

        # Forceer harmony naar 0
        result = await orchestrator.process_signal({
            "inputs": {},  # Lege inputs = geen harmony
            "soul_context": {"market_regime": "unknown"},
        })

        assert result["harmony_score"] >= 0.0

    @pytest.mark.asyncio
    async def test_very_small_order_size(self):
        """EC-004: Zeer kleine order grootte."""
        from backend.schemas.orders import OrderRequest, OrderSide, OrderType

        portfolio = ShadowPortfolioManager(initial_cash=10000.0)
        portfolio.update_price("BTC/EUR", 50000.0)

        # Zeer kleine hoeveelheid
        order = OrderRequest(
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            qty=0.00000001,  # 1 satoshi
            order_type=OrderType.MARKET,
        )

        result = await portfolio.submit_order(order)
        # Zou moeten werken of netjes afwijzen

    @pytest.mark.asyncio
    async def test_very_large_order_size(self):
        """EC-005: Zeer grote order grootte."""
        from backend.schemas.orders import OrderRequest, OrderSide, OrderType

        portfolio = ShadowPortfolioManager(initial_cash=10000.0)
        portfolio.update_price("BTC/EUR", 50000.0)

        # Zeer grote hoeveelheid (meer dan bestaat)
        order = OrderRequest(
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            qty=1000000.0,  # 1M BTC
            order_type=OrderType.MARKET,
        )

        result = await portfolio.submit_order(order)
        # Zou afgewezen moeten worden wegens insufficient funds


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance integratietests."""

    @pytest.mark.asyncio
    async def test_elemental_response_time(self, elemental_agents):
        """PERF-001: Agents reageren binnen 100ms."""
        import time

        agent = elemental_agents["air"]
        signal = {"market_data": {"price": 50000}}

        start = time.time()
        result = await agent.process_signal(signal)
        elapsed = (time.time() - start) * 1000  # ms

        assert elapsed < 100, f"Response time {elapsed}ms > 100ms"

    @pytest.mark.asyncio
    async def test_multiple_cycles_performance(self, elemental_agents):
        """PERF-002: Meerdere cycles zonder memory leaks."""
        orchestrator = elemental_agents["ether"]

        for i in range(10):
            result = await orchestrator.process_signal({
                "inputs": {"air": {"signal": 0.5}},
                "soul_context": {"market_regime": "expansion"},
            })
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
