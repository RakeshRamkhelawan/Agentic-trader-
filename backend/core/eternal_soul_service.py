import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as redis

from backend.core.config.settings import settings
from backend.core.karma.episode_memory import EpisodeMemory
from backend.core.navagraha.service import NavagrahaService
from backend.core.regime_detector import MarketRegime, RegimeDetector

logger = logging.getLogger(__name__)


class EternalSoulService:
    """
    Layer 1: The Eternal Soul (Atman/Purusha).
    Operates at a slow frequency (e.g., 1 minute).

    Responsibilities:
    - Maintain the "System Consciousness" level.
    - Track Cosmic Time (Rahu Kala, Muhurtas).
    - Detect high-level Market Regime (Bull/Bear/Volatile).
    - Publish 'Soul Context' to Redis for faster layers (Mind/Body) to consume.
    """

    def __init__(self):
        self.redis_client: redis.Redis | None = None
        self.navagraha = NavagrahaService()
        self.regime_detector = RegimeDetector()
        self.episode_memory = EpisodeMemory()

        # State
        self.price_history: list[float] = []
        self.max_history = 250  # Need 200 for SMA200

        self.running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the Eternal Soul service loop."""
        if self.running:
            return

        logger.info("Awakening the Eternal Soul...")

        # Connect to Redis
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Eternal Soul connected to Redis.")
        except Exception as e:
            logger.error(f"Eternal Soul failed to connect to Redis: {e}")
            # We might want to raise here, or retry. For now, we log and continue (loop will fail).

        self.running = True
        self._task = asyncio.create_task(self._cosmic_cycle_loop())

    async def stop(self):
        """Stop the service."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self.redis_client:
            await self.redis_client.close()

        logger.info("The Eternal Soul has withdrawn.")

    async def _cosmic_cycle_loop(self):
        """
        The main heartbeat of the Soul.
        Runs once per minute to update high-level context.
        """
        while self.running:
            try:
                await self.process_cycle()
            except Exception as e:
                logger.error(f"Error in Eternal Soul Cycle: {e}", exc_info=True)

            # Wait for next minute alignment or generic 60s
            await asyncio.sleep(60)

    async def process_cycle(self):
        """
        Execute a single cosmic cycle step.
        """
        start_time = datetime.now(UTC)

        # 1. Calculate Navagraha State (Cosmic Time)
        # We use default lat/lon from settings
        navagraha_state = await self.navagraha.get_current_state(
            lat=settings.LATITUDE, lon=settings.LONGITUDE, dt=start_time
        )

        # 2. Detect Market Regime (Material Context)
        # Fetch current market data
        market_ctx = await self._fetch_market_context()
        current_price = market_ctx["price"]

        # Update History
        self.price_history.append(current_price)
        if len(self.price_history) > self.max_history:
            self.price_history.pop(0)

        # Calculate Indicators & Detect Regime
        sma_50, sma_200, vol = self.regime_detector.calculate_indicators(self.price_history)
        regime = self.regime_detector.detect(current_price, sma_50, sma_200, vol)

        # 3. Check Karma patterns (Phase 6)
        try:
            causality_threshold = self.episode_memory.get_causality_threshold(
                current_regime=regime.value
            )
        except Exception as e:
            logger.error(f"Karma check error: {e}, using default threshold")
            causality_threshold = 0.6

        # 4. Synthesize Soul Context
        soul_context = {
            "timestamp": start_time.isoformat(),
            "rahu_kala_active": navagraha_state.rahu_kala_active,
            "consciousness_level": navagraha_state.consciousness_level,
            "guna_dominance": navagraha_state.guna_distribution.dominant_guna,
            "trading_gate_open": navagraha_state.trading_gate_open,
            "market_regime": regime.value,
            "causality_threshold": causality_threshold,
            "market_metrics": {
                "price": current_price,
                "sma_50": sma_50,
                "sma_200": sma_200,
                "volatility": vol,
            },
        }

        # 4. publish to Redis (The "Ether")
        # fast layers (Mind/Body) read this.
        # We set a TTL slightly longer than the cycle (e.g. 90s for 60s cycle)
        if self.redis_client:
            await self.redis_client.set("soul:context", json.dumps(soul_context), ex=90)

            # Also publish event for optional subscribers
            await self.redis_client.publish("soul.updates", json.dumps(soul_context))

        # Update Prometheus Metrics
        from backend.core.telemetry.metrics import PrometheusMetrics

        metrics = PrometheusMetrics("eternal_soul")

        # Mapping Regime to Int
        regime_map = {
            MarketRegime.SIDEWAYS: 0,
            MarketRegime.BULL: 1,
            MarketRegime.BEAR: 2,
            MarketRegime.VOLATILE: 3,
        }
        regime_int = regime_map.get(regime, 0)
        metrics.market_regime_state.set(regime_int)

        # Export Guna metrics to Prometheus
        guna = navagraha_state.guna_distribution
        metrics.global_guna_sattva.set(guna.sattva)
        metrics.global_guna_rajas.set(guna.rajas)
        metrics.global_guna_tamas.set(guna.tamas)
        metrics.guna_deviation_score.set(1.0 - guna.balance_score)

        logger.info(
            f"Soul Cycle Complete. Regime: {regime}, Gate: {soul_context['trading_gate_open']}"
        )
        return soul_context

    async def _fetch_market_context(self) -> dict[str, Any]:
        """
        Fetch necessary market data for regime detection.
        Current implementation is a placeholder with Random Walk.
        """
        # Simple Random Walk for testing
        if not self.price_history:
            current_price = 42000.0
        else:
            current_price = self.price_history[-1]

        # Random change +/- 0.5%
        import random

        change = random.uniform(-0.005, 0.005)
        current_price *= 1 + change

        return {
            "symbol": "BTC/USD",
            "price": current_price,
            "volatility": abs(change) * 10,  # Rough proxy
        }
