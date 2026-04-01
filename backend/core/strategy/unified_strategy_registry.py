"""
Unified Strategy Registry - Phase D Integration.

Verbindt DashaStrategyMap met NavagrahaService voor dynamische strategy selectie
gebaseerd op planetaire periodes. Werkt als plugin systeem voor TraderAgent.

Enhanced met multi-indicator strategieen (Sprint 1).
"""

import logging
from typing import Any

from backend.core.navagraha.service import NavagrahaService
from backend.core.strategy.dasha_strategy_map import DashaStrategyMap
from backend.core.strategy.implementations import (
    DefensiveStrategy,
    MeanReversionStrategy,
    TrendFollowingStrategy,
)
from backend.core.strategy.interface import TradingStrategy
from backend.core.zero_copy_bridge import TradingIntent

logger = logging.getLogger(__name__)


class UnifiedStrategyRegistry:
    """
    Central strategy registry that integrates Dasha-based selection.

    Features:
    - Register strategies by ID (basic + enhanced multi-indicator)
    - Get strategy based on Dasha period from Navagraha
    - Fallback strategies for different regimes
    """

    def __init__(
        self,
        navagraha_service: NavagrahaService | None = None,
        dasha_map: DashaStrategyMap | None = None,
    ):
        self.navagraha_service = navagraha_service
        self.dasha_map = dasha_map or DashaStrategyMap()

        # Strategy registry - basic strategies
        self._strategies: dict[str, TradingStrategy] = {
            "trend_following": TrendFollowingStrategy(),
            "mean_reversion": MeanReversionStrategy(),
            "defensive": DefensiveStrategy(),
        }

        # Dasha to strategy ID mapping
        self._dasha_strategy_map = {
            "Sun": "trend_following",
            "Moon": "mean_reversion",
            "Mars": "trend_following",
            "Mercury": "mean_reversion",
            "Jupiter": "trend_following",
            "Venus": "mean_reversion",
            "Saturn": "defensive",
            "Rahu": "defensive",  # Erratic - use defensive
            "Ketu": "defensive",  # Detachment - use defensive
        }

        logger.info(
            "UnifiedStrategyRegistry initialized with %d strategies",
            len(self._strategies),
        )

    def register_strategy(self, strategy_id: str, strategy: TradingStrategy) -> None:
        """Register a new strategy."""
        self._strategies[strategy_id] = strategy
        logger.info(f"Registered strategy: {strategy_id}")

    def get_strategy(self, strategy_id: str) -> TradingStrategy | None:
        """Get strategy by ID."""
        return self._strategies.get(strategy_id)

    async def get_strategy_for_current_dasha(
        self,
        lat: float = 52.3676,  # Amsterdam default
        lon: float = 4.9041,
    ) -> tuple[str, TradingStrategy]:
        """
        Get recommended strategy based on current Dasha period.

        Returns:
            Tuple of (strategy_id, strategy_instance)
        """
        if not self.navagraha_service:
            logger.warning("No NavagrahaService configured, using default strategy")
            return "trend_following", self._strategies["trend_following"]

        try:
            # Get current Navagraha state
            nava_state = await self.navagraha_service.get_current_state(lat=lat, lon=lon)

            # Get current Dasha lord
            current_dasha = nava_state.current_dasha
            if not current_dasha:
                logger.debug("No current Dasha available, using default")
                return "trend_following", self._strategies["trend_following"]

            dasha_name = current_dasha.value
            strategy_id = self._dasha_strategy_map.get(dasha_name, "trend_following")

            # Get strategy config for logging
            strategy_config = self.dasha_map.get_strategy_config(dasha_name, dasha_name)

            logger.info(
                f"Dasha-based strategy selection: {dasha_name} -> {strategy_id} "
                f"(risk: {strategy_config.risk_profile.value}, "
                f"horizon: {strategy_config.time_horizon.value})"
            )

            return strategy_id, self._strategies[strategy_id]

        except Exception as e:
            logger.warning(f"Dasha strategy selection failed: {e}, using default")
            return "trend_following", self._strategies["trend_following"]

    async def analyze_with_dasha_strategy(
        self,
        market_data: dict[str, Any],
        soul_context: dict[str, Any],
        lat: float = 52.3676,
        lon: float = 4.9041,
    ) -> TradingIntent | None:
        """
        Analyze market using Dasha-appropriate strategy.

        Args:
            market_data: Market data dict
            soul_context: Context including regime, guna, etc.
            lat: Latitude for Navagraha
            lon: Longitude for Navagraha

        Returns:
            TradingIntent or None
        """
        strategy_id, strategy = await self.get_strategy_for_current_dasha(lat, lon)

        try:
            # Add strategy info to soul context
            enriched_context = {
                **soul_context,
                "selected_strategy": strategy_id,
                "dasha_based": True,
            }

            intent = await strategy.analyze(market_data, enriched_context)

            logger.debug(
                f"Strategy {strategy_id} generated intent: "
                f"action={intent.action}, confidence={intent.confidence:.2f}"
            )

            return intent

        except Exception as e:
            logger.error(f"Strategy {strategy_id} analysis failed: {e}")
            return None

    def get_strategy_config_for_current_dasha(
        self,
        mahadasha: str = "Sun",
        antardasha: str = "Sun",
    ) -> dict[str, Any]:
        """Get strategy config for Dasha periods."""
        config = self.dasha_map.get_strategy_config(mahadasha, antardasha)
        return {
            "risk_profile": config.risk_profile.value,
            "time_horizon": config.time_horizon.value,
            "asset_preference": [a.value for a in config.asset_preference],
            "description": config.description,
        }
