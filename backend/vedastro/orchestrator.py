"""
Tattva Orchestrator - Consciousness Controller

Integration point between VedAstro (outer world) and 36 Tattvas (inner world).
Decides whether to trade based on cosmic and philosophical alignment.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .connector import VedAstroConfig, VedAstroConnector
from .features import FeatureEngine
from .oracle import XGBoostOracle

logger = logging.getLogger(__name__)


@dataclass
class TradingDecision:
    """Final trading decision with reasoning."""

    action: str  # 'UP', 'DOWN', 'HOLD', 'WAIT'
    confidence: float
    size: float
    reason: str
    tattva_aligned: bool
    original_signal: str
    alignment_score: float


class TattvaOrchestrator:
    """
    Orchestrates the fusion of VedAstro calculations, XGBoost ML,
    and 36 Tattvas consciousness system.

    The orchestrator:
    1. Fetches Kundli data (cached)
    2. Calculates current transits
    3. Updates 36 Tattvas state
    4. Extracts ML features
    5. Gets XGBoost prediction
    6. Applies philosophical filters
    """

    # Asset birth dates (genesis/IPO)
    ASSET_BIRTHDAYS = {
        "BTC": datetime(2009, 1, 3, 18, 15),  # Genesis block
        "ETH": datetime(2015, 7, 30, 15, 26),  # Genesis block
        "AAPL": datetime(1980, 12, 12, 9, 30),  # IPO
        "TSLA": datetime(2010, 6, 29, 9, 30),  # IPO
        "GOOGL": datetime(2004, 8, 19, 9, 30),  # IPO
        "MSFT": datetime(1986, 3, 13, 9, 30),  # IPO
        "AMZN": datetime(1997, 5, 15, 9, 30),  # IPO
        "NVDA": datetime(1999, 1, 22, 9, 30),  # IPO
    }

    def __init__(
        self,
        system_identity=None,
        guna_quantifier=None,
        vedastro_config: VedAstroConfig | None = None,
        model_path: str | None = None,
        min_coherence: float = 0.6,
        tamas_threshold: float = 0.5,
        sade_sati_protection: bool = True,
    ):
        """
        Initialize Tattva Orchestrator.

        Args:
            system_identity: SystemIdentity instance (36 Tattvas)
            guna_quantifier: GunaQuantifier instance
            vedastro_config: VedAstro configuration
            model_path: Path to pre-trained XGBoost model
            min_coherence: Minimum Tattva coherence for trading
            tamas_threshold: Maximum Tamas for trading
            sade_sati_protection: Enable Sade Sati protection
        """
        self.system_identity = system_identity
        self.guna_quantifier = guna_quantifier
        self.min_coherence = min_coherence
        self.tamas_threshold = tamas_threshold
        self.sade_sati_protection = sade_sati_protection

        # Initialize components
        self.vedastro = VedAstroConnector(vedastro_config or VedAstroConfig())
        self.feature_engine = FeatureEngine()
        self.oracle = XGBoostOracle(model_path)

        # Cache for Kundli data
        self.kundli_cache: dict[str, dict] = {}
        self.active_assets: list[str] = []

        # Statistics
        self.stats = {
            "ticks_processed": 0,
            "trades_allowed": 0,
            "trades_blocked": 0,
            "block_reasons": {},
        }

    async def initialize(self, assets: list[str] | None = None):
        """
        Pre-calculate Kundli's for active assets.

        Args:
            assets: List of asset symbols to initialize
        """
        self.active_assets = assets or list(self.ASSET_BIRTHDAYS.keys())

        for symbol in self.active_assets:
            birth_date = self.ASSET_BIRTHDAYS.get(symbol)
            if not birth_date:
                logger.warning(f"No birth date for {symbol}, skipping")
                continue

            try:
                self.kundli_cache[symbol] = await self.vedastro.calculate_kundli(symbol, birth_date)
                logger.info(f"Pre-calculated Kundli for {symbol}")
            except Exception as e:
                logger.error(f"Failed to calculate Kundli for {symbol}: {e}")

        logger.info(f"Orchestrator initialized with {len(self.kundli_cache)} assets")

    async def process_market_tick(self, symbol: str, tick_data: dict[str, Any]) -> dict[str, Any]:
        """
        Main entry point for market tick processing.

        Args:
            symbol: Asset symbol
            tick_data: Market tick data with price, volume, etc.

        Returns:
            Complete analysis with decision
        """
        self.stats["ticks_processed"] += 1

        # 1. Get Kundli (O(1) from cache)
        kundli = self.kundli_cache.get(symbol)
        if not kundli:
            return {"error": "No Kundli available for symbol", "symbol": symbol}

        # 2. Calculate current transits
        current_time = datetime.now()
        transits = await self.vedastro.calculate_transits(current_time, kundli)

        # 3. Update 36 Tattvas (if system_identity provided)
        tattva_state = await self._update_tattvas(tick_data, transits)

        # 4. Extract ML features
        technical = tick_data.get("indicators", {})
        features = self.feature_engine.extract(
            kundli, transits, tick_data.get("price", 0), tattva_state, technical
        )

        # 5. XGBoost prediction (fast)
        ml_signal = self.oracle.predict(features)

        # 6. Apply philosophical filters
        decision = self._apply_tattva_filter(ml_signal, tattva_state, transits)

        # 7. Calculate alignment score
        alignment = self._calculate_alignment(ml_signal, tattva_state)

        if decision.tattva_aligned:
            self.stats["trades_allowed"] += 1
        else:
            self.stats["trades_blocked"] += 1
            reason_key = decision.reason[:50]  # Truncate
            self.stats["block_reasons"][reason_key] = (
                self.stats["block_reasons"].get(reason_key, 0) + 1
            )

        return {
            "symbol": symbol,
            "timestamp": current_time.isoformat(),
            "ml_signal": ml_signal,
            "tattva_state": tattva_state,
            "transits": {
                "retrograde_count": transits.get("retrograde_count", 0),
                "exalted_planets": transits.get("exalted_planets", []),
                "debilitated_planets": transits.get("debilitated_planets", []),
                "aspect_count": len(transits.get("aspects", [])),
            },
            "decision": {
                "action": decision.action,
                "confidence": decision.confidence,
                "size": decision.size,
                "reason": decision.reason,
                "tattva_aligned": decision.tattva_aligned,
            },
            "alignment_score": alignment,
            "features": self.feature_engine.explain_features(features),
        }

    async def _update_tattvas(self, tick_data: dict, transits: dict) -> dict[str, Any]:
        """
        Update 36 Tattvas system with astro input.

        Args:
            tick_data: Market data
            transits: Astro transits

        Returns:
            Tattva state
        """
        # Default state if no system_identity
        if not self.system_identity:
            return self._default_tattva_state(transits)

        # Create perception from astro + market data
        perception = {
            "price": tick_data.get("price", 0),
            "volume": tick_data.get("volume", 0),
            "astro_coherence": self._calculate_astro_coherence(transits),
            "retrograde_stress": transits.get("retrograde_count", 0) / 9.0,
            "exalted_benefics": len(
                [p for p in transits.get("exalted_planets", []) if p in ["Jupiter", "Venus"]]
            ),
            "malefic_pressure": len(
                [p for p in transits.get("debilitated_planets", []) if p in ["Saturn", "Mars"]]
            ),
        }

        try:
            # Call SystemIdentity (if available)
            tattva_result = await self.system_identity.process_market_cycle(
                price_data=perception, coherence_threshold=self.min_coherence
            )

            # Get Gunas (if guna_quantifier available)
            if self.guna_quantifier:
                gunas = await self.guna_quantifier.quantify_state(perception)
                gunas_dict = {
                    "sattva": getattr(gunas, "sattva", 0.33),
                    "rajas": getattr(gunas, "rajas", 0.33),
                    "tamas": getattr(gunas, "tamas", 0.33),
                }
            else:
                gunas_dict = self._derive_gunas_from_transits(transits)

            return {
                "coherence": tattva_result.get("coherence", 0.5),
                "dominant_layer": tattva_result.get("dominant_layer", "Manas"),
                "gunas": gunas_dict,
                "ascending": tattva_result.get("ascending", False),
            }

        except Exception as e:
            logger.error(f"Error updating Tattvas: {e}")
            return self._default_tattva_state(transits)

    def _default_tattva_state(self, transits: dict) -> dict[str, Any]:
        """Generate default Tattva state from transits."""
        coherence = self._calculate_astro_coherence(transits)
        gunas = self._derive_gunas_from_transits(transits)

        return {
            "coherence": coherence,
            "dominant_layer": "Manas",
            "gunas": gunas,
            "ascending": coherence > 0.6,
        }

    def _derive_gunas_from_transits(self, transits: dict) -> dict[str, float]:
        """Derive Guna balance from planetary transits."""
        sattva = 0.33
        rajas = 0.33
        tamas = 0.33

        # Benefics in good dignity increase Sattva
        benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
        for planet in transits.get("exalted_planets", []):
            if planet in benefics:
                sattva += 0.1

        # Malefics in difficult positions increase Tamas
        malefics = ["Saturn", "Mars", "Rahu", "Ketu"]
        for planet in transits.get("debilitated_planets", []):
            if planet in malefics:
                tamas += 0.1

        # Retrogrades increase Rajas (churning/activity)
        retro_count = transits.get("retrograde_count", 0)
        rajas += retro_count * 0.02

        # Normalize
        total = sattva + rajas + tamas
        return {
            "sattva": sattva / total,
            "rajas": rajas / total,
            "tamas": tamas / total,
        }

    def _calculate_astro_coherence(self, transits: dict) -> float:
        """
        Calculate cosmic coherence (0-1).

        More exalted planets = higher coherence.
        """
        base = 0.5
        exalted = len(transits.get("exalted_planets", []))
        debilitated = len(transits.get("debilitated_planets", []))
        retrograde = transits.get("retrograde_count", 0)

        coherence = base + (exalted * 0.1) - (debilitated * 0.15) - (retrograde * 0.02)
        return max(0.0, min(1.0, coherence))

    def _apply_tattva_filter(
        self, ml_signal: dict, tattva_state: dict, transits: dict
    ) -> TradingDecision:
        """
        Apply philosophical filters to ML signal.

        Returns HOLD if:
        - Tamas > threshold (preservation mode)
        - Coherence < minimum (unclear consciousness)
        - Sade Sati active (Saturn around Moon)
        """
        gunas = tattva_state.get("gunas", {"sattva": 0.33, "rajas": 0.33, "tamas": 0.33})
        action = ml_signal["direction"]
        confidence = ml_signal["confidence"]
        coherence = tattva_state.get("coherence", 0.5)

        # RULE 1: Tamas dominance = preservation mode
        if gunas.get("tamas", 0) > self.tamas_threshold:
            return TradingDecision(
                action="HOLD",
                confidence=confidence,
                size=0.0,
                reason="Tamas dominance - preservation mode",
                tattva_aligned=False,
                original_signal=action,
                alignment_score=0.0,
            )

        # RULE 2: Sade Sati protection (Saturn transit around Moon)
        if self.sade_sati_protection and self._is_sade_sati(transits):
            if action == "UP":  # Sade Sati is generally bearish
                return TradingDecision(
                    action="HOLD",
                    confidence=confidence,
                    size=0.0,
                    reason="Sade Sati protection active",
                    tattva_aligned=False,
                    original_signal=action,
                    alignment_score=0.2,
                )

        # RULE 3: Minimum coherence required
        if coherence < self.min_coherence:
            return TradingDecision(
                action="WAIT",
                confidence=confidence,
                size=0.0,
                reason=f"Low coherence ({coherence:.2f}) - unclear consciousness",
                tattva_aligned=False,
                original_signal=action,
                alignment_score=coherence,
            )

        # RULE 4: Size scaling based on Guna balance
        # Sattva = full size, Rajas = reduced, Tamas = minimal
        size_multiplier = (
            gunas.get("sattva", 0) * 1.0 + gunas.get("rajas", 0) * 0.5 + gunas.get("tamas", 0) * 0.0
        )

        # RULE 5: Retrograde stress reduction
        retro_count = transits.get("retrograde_count", 0)
        if retro_count > 3:
            confidence *= 0.7
            size_multiplier *= 0.8

        final_size = confidence * size_multiplier

        return TradingDecision(
            action=action,
            confidence=confidence,
            size=final_size,
            reason=(
                f"ML:{action}({confidence:.2f}) + "
                f'Guna:S{gunas.get("sattva", 0):.1f}R{gunas.get("rajas", 0):.1f} + '
                f"Coherence:{coherence:.2f}"
            ),
            tattva_aligned=True,
            original_signal=action,
            alignment_score=self._calculate_alignment(ml_signal, tattva_state),
        )

    def _is_sade_sati(self, transits: dict) -> bool:
        """
        Check if Sade Sati is active.

        Sade Sati = Saturn transiting 12th, 1st, or 2nd from Moon.
        This is a placeholder - full implementation needs Dasha calculator.
        """
        # Simplified check: Saturn debilitated or in difficult aspect
        saturn_debilitated = "Saturn" in transits.get("debilitated_planets", [])
        saturn_retrograde = False

        for planet, pos in transits.get("current_positions", {}).items():
            if planet == "Saturn" and pos.get("retrograde"):
                saturn_retrograde = True
                break

        return saturn_debilitated and saturn_retrograde

    def _calculate_alignment(self, ml_signal: dict, tattva_state: dict) -> float:
        """
        Calculate alignment score between ML and philosophy.

        1.0 = perfect harmony, 0.0 = total conflict
        """
        alignment = 1.0
        gunas = tattva_state.get("gunas", {})

        # ML says UP but Tamas high = conflict
        if ml_signal["direction"] == "UP" and gunas.get("tamas", 0) > 0.4:
            alignment -= 0.3

        # ML says DOWN but Sattva high = conflict (Sattva is bullish)
        if ml_signal["direction"] == "DOWN" and gunas.get("sattva", 0) > 0.5:
            alignment -= 0.3

        # Low coherence = misalignment
        alignment *= tattva_state.get("coherence", 0.5)

        return max(0.0, alignment)

    def get_stats(self) -> dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            **self.stats,
            "cached_kundlis": len(self.kundli_cache),
            "active_assets": self.active_assets,
            "oracle_info": self.oracle.get_model_info(),
            "vedastro_cache": self.vedastro.get_cache_stats(),
        }

    async def shutdown(self):
        """Cleanup resources."""
        logger.info("Shutting down TattvaOrchestrator")
        self.vedastro.clear_cache()
