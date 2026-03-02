#!/usr/bin/env python3
"""
E2E WebSocket Integratietests
Test de volledige flow van backend naar frontend via WebSocket

Usage:
    pytest tests/integration/test_websocket_e2e.py -v
"""

import asyncio
import json
import os
import pytest
from datetime import datetime, timezone

os.environ["TRADING_MODE"] = "paper"

from backend.services.paper_trading_live import PaperTradingLiveBroadcaster


class TestWebSocketE2E:
    """End-to-End WebSocket tests."""

    @pytest.mark.asyncio
    async def test_broadcast_trade_e2e(self):
        """WS-E2E-001: Trade broadcast flow."""
        broadcaster = PaperTradingLiveBroadcaster()

        trade_data = {
            "symbol": "BTC/EUR",
            "side": "buy",
            "qty": 0.001,
            "price": 50000.0,
            "value": 50.0,
            "agent": "MomentumTrader",
            "exchange": "Bitvavo",
        }

        # Broadcast zou geen exception moeten gooien
        await broadcaster.broadcast_trade(trade_data)
        # In productie zou dit via WebSocket naar frontend gaan

    @pytest.mark.asyncio
    async def test_broadcast_portfolio_update_e2e(self):
        """WS-E2E-002: Portfolio update broadcast flow."""
        broadcaster = PaperTradingLiveBroadcaster()

        portfolio_data = {
            "cash": 9950.0,
            "total_value": 10012.50,
            "pnl": 12.50,
            "pnl_pct": 0.125,
            "positions": {"BTC/EUR": {"qty": 0.001, "avg_price": 50000.0}},
        }

        await broadcaster.broadcast_portfolio_update(portfolio_data)

    @pytest.mark.asyncio
    async def test_broadcast_vedic_soul_update_e2e(self):
        """WS-E2E-003: Vedic soul context broadcast flow."""
        broadcaster = PaperTradingLiveBroadcaster()

        soul_context = {
            "rahu_kala_active": False,
            "market_regime": "expansion",
            "vedic_time": "Brahma Muhurta",
            "navagraha_dominant": "Jupiter",
            "consciousness_level": 0.75,
            "trading_gate_open": True,
        }

        await broadcaster.broadcast_soul_update(soul_context)

    @pytest.mark.asyncio
    async def test_broadcast_vedic_prana_update_e2e(self):
        """WS-E2E-004: Vedic prana levels broadcast flow."""
        broadcaster = PaperTradingLiveBroadcaster()

        prana_levels = {
            "ether": 85.0,
            "air": 72.5,
            "fire": 91.0,
            "water": 68.0,
            "earth": 55.5,
        }

        await broadcaster.broadcast_prana_update(prana_levels)

    @pytest.mark.asyncio
    async def test_broadcast_vedic_harmony_update_e2e(self):
        """WS-E2E-005: Vedic harmony score broadcast flow."""
        broadcaster = PaperTradingLiveBroadcaster()

        synthesis = {
            "focus_element": "fire",
            "action": "Execute",
            "confidence": 0.82,
        }

        await broadcaster.broadcast_harmony_update(0.75, synthesis)

    @pytest.mark.asyncio
    async def test_broadcast_cosmic_block_e2e(self):
        """WS-E2E-006: Cosmic block event broadcast flow."""
        broadcaster = PaperTradingLiveBroadcaster()

        await broadcaster.broadcast_cosmic_block(
            reason="Rahu Kala",
            blocked_at=datetime.now(timezone.utc).isoformat(),
            resumes_at="2026-02-20T13:30:00Z",
        )

    @pytest.mark.asyncio
    async def test_broadcast_agent_decision_e2e(self):
        """WS-E2E-007: Agent decision broadcast flow."""
        broadcaster = PaperTradingLiveBroadcaster()

        decision = {
            "symbol": "BTC/EUR",
            "side": "BUY",
            "confidence": 0.85,
            "reason": "momentum_breakout",
            "price": 50000.0,
        }

        await broadcaster.broadcast_agent_decision("MomentumTrader", decision)

    @pytest.mark.asyncio
    async def test_broadcast_stats_e2e(self):
        """WS-E2E-008: Stats broadcast flow."""
        broadcaster = PaperTradingLiveBroadcaster()

        stats = {
            "elapsed": "0:30:00",
            "total_trades": 47,
            "symbols_traded": 12,
            "buy_sell_ratio": "28/19",
            "total_value": 10087.50,
            "pnl": 87.50,
            "pnl_pct": 0.875,
            "agent_performance": {
                "MomentumTrader": 15,
                "MeanReversion": 12,
            },
        }

        await broadcaster.broadcast_stats(stats)

    @pytest.mark.asyncio
    async def test_full_session_lifecycle_e2e(self):
        """WS-E2E-009: Complete sessie lifecycle broadcasts."""
        broadcaster = PaperTradingLiveBroadcaster()

        # Session start
        await broadcaster.broadcast_session_start({
            "capital": 10000.0,
            "exchanges": ["bitvavo"],
            "symbols_count": 50,
            "agents": ["MomentumTrader", "MeanReversion"],
        })

        # Enkele trades
        for i in range(3):
            await broadcaster.broadcast_trade({
                "symbol": f"COIN{i}/EUR",
                "side": "buy" if i % 2 == 0 else "sell",
                "qty": 0.001,
                "price": 100.0 * (i + 1),
                "value": 0.1 * (i + 1),
                "agent": "MomentumTrader",
                "exchange": "Bitvavo",
            })

        # Portfolio update
        await broadcaster.broadcast_portfolio_update({
            "cash": 9950.0,
            "total_value": 10050.0,
            "pnl": 50.0,
            "pnl_pct": 0.5,
            "positions": {"COIN0/EUR": {"qty": 0.001, "avg_price": 100.0}},
        })

        # Vedic updates
        await broadcaster.broadcast_soul_update({
            "rahu_kala_active": False,
            "market_regime": "expansion",
            "vedic_time": "Brahma Muhurta",
            "navagraha_dominant": "Jupiter",
        })

        await broadcaster.broadcast_prana_update({
            "ether": 90.0, "air": 85.0, "fire": 88.0, "water": 82.0, "earth": 80.0,
        })

        # Session end
        await broadcaster.broadcast_session_end({
            "total_trades": 3,
            "final_pnl": 50.0,
        })


class TestWebSocketUnhappyPaths:
    """WebSocket unhappy path tests."""

    @pytest.mark.asyncio
    async def test_broadcast_with_none_values(self):
        """WS-UP-001: Broadcast met None values."""
        broadcaster = PaperTradingLiveBroadcaster()

        # Zou geen exception moeten gooien
        await broadcaster.broadcast_trade({
            "symbol": None,
            "side": "buy",
            "qty": 0.001,
            "price": 50000.0,
            "value": None,
            "agent": "TestAgent",
        })

    @pytest.mark.asyncio
    async def test_broadcast_empty_data(self):
        """WS-UP-002: Broadcast met lege data."""
        broadcaster = PaperTradingLiveBroadcaster()

        # Zou geen exception moeten gooien
        await broadcaster.broadcast_trade({})

    @pytest.mark.asyncio
    async def test_rapid_broadcasts(self):
        """WS-UP-003: Snelle opeenvolgende broadcasts."""
        broadcaster = PaperTradingLiveBroadcaster()

        # 100 snelle broadcasts
        for i in range(100):
            await broadcaster.broadcast_trade({
                "symbol": "BTC/EUR",
                "side": "buy",
                "qty": 0.001,
                "price": 50000.0 + i,
                "value": 50.0,
                "agent": "SpeedTrader",
            })
        # Zou geen memory issues of race conditions moeten veroorzaken


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
