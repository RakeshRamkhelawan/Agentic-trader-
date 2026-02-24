"""
Feature Engine - Astro to ML Features

Converts VedAstro planetary data into normalized ML features
for XGBoost consumption. All operations are vectorized for O(1) performance.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.preprocessing import StandardScaler


@dataclass
class AstroFeatures:
    """Standardized features for XGBoost."""

    # Geometric features (normalized 0-1)
    sun_moon_angle: float = 0.0
    sun_jupiter_angle: float = 0.0
    moon_saturn_angle: float = 0.0
    mars_jupiter_angle: float = 0.0

    # Aspect indicators (binary)
    jupiter_trine_sun: int = 0
    saturn_square_moon: int = 0
    venus_trine_jupiter: int = 0
    mars_sextile_sun: int = 0

    # Benefic/Malefic aspects
    benefic_aspects: int = 0
    malefic_aspects: int = 0

    # Transit state
    retrograde_count: int = 0
    exalted_count: int = 0
    debilitated_count: int = 0

    # Dignity scores
    jupiter_dignity: float = 0.0  # -1 to 1
    saturn_dignity: float = 0.0
    venus_dignity: float = 0.0

    # Gann features
    price_at_cardinal: int = 0
    price_angle: float = 0.0

    # 36 Tattvas integration
    tattva_coherence: float = 0.5
    dominant_guna: int = 1  # 0=Sattva, 1=Rajas, 2=Tamas

    # Technical integration
    volatility_regime: float = 0.5
    trend_strength: float = 0.0

    # Composite scores
    astro_bullish_score: float = 0.5
    astro_bearish_score: float = 0.5


class FeatureEngine:
    """
    Vectorized feature extraction from astrological data.

    Converts VedAstro planetary positions and transits into
    normalized feature vectors suitable for XGBoost.
    """

    FEATURE_NAMES = [
        "sun_moon_angle",
        "sun_jupiter_angle",
        "moon_saturn_angle",
        "mars_jupiter_angle",
        "jupiter_trine_sun",
        "saturn_square_moon",
        "venus_trine_jupiter",
        "mars_sextile_sun",
        "benefic_aspects",
        "malefic_aspects",
        "retrograde_count",
        "exalted_count",
        "debilitated_count",
        "jupiter_dignity",
        "saturn_dignity",
        "venus_dignity",
        "price_at_cardinal",
        "price_angle",
        "tattva_coherence",
        "dominant_guna",
        "volatility_regime",
        "trend_strength",
        "astro_bullish_score",
        "astro_bearish_score",
    ]

    def __init__(self):
        self.scaler = StandardScaler()
        self._fitted = False

    def extract(
        self,
        kundli: dict[str, Any],
        transits: dict[str, Any],
        current_price: float,
        tattva_state: dict[str, Any],
        technical_indicators: dict | None = None,
    ) -> np.ndarray:
        """
        Extract features from astrological and market data.

        Args:
            kundli: Birth chart data
            transits: Current transit data
            current_price: Current market price
            tattva_state: SystemIdentity state
            technical_indicators: Optional technical analysis data

        Returns:
            Normalized feature vector (24 features)
        """
        features = AstroFeatures()

        # 1. Planetary angles (0-360 normalized to 0-1)
        planets = kundli.get("planets", {})

        if "Sun" in planets and "Moon" in planets:
            features.sun_moon_angle = self._calculate_angle(planets["Sun"], planets["Moon"]) / 360.0

        if "Sun" in planets and "Jupiter" in planets:
            features.sun_jupiter_angle = (
                self._calculate_angle(planets["Sun"], planets["Jupiter"]) / 360.0
            )

        if "Moon" in planets and "Saturn" in planets:
            features.moon_saturn_angle = (
                self._calculate_angle(planets["Moon"], planets["Saturn"]) / 360.0
            )

        if "Mars" in planets and "Jupiter" in planets:
            features.mars_jupiter_angle = (
                self._calculate_angle(planets["Mars"], planets["Jupiter"]) / 360.0
            )

        # 2. Aspect analysis from transits
        benefic_count = 0
        malefic_count = 0

        for aspect in transits.get("aspects", []):
            planet = aspect.get("planet", "")
            aspect_type = aspect.get("type", "")

            # Benefic aspects (Jupiter/Venus + trine/sextile)
            if planet in ["Jupiter", "Venus"]:
                if aspect_type in ["trine", "sextile"]:
                    benefic_count += 1
                    if planet == "Jupiter" and aspect_type == "trine":
                        features.jupiter_trine_sun = 1
                    if planet == "Venus" and aspect_type == "trine":
                        features.venus_trine_jupiter = 1

            # Malefic aspects (Saturn/Mars + square/opposition)
            if planet in ["Saturn", "Mars"]:
                if aspect_type in ["square", "opposition"]:
                    malefic_count += 1
                    if planet == "Saturn" and aspect_type == "square":
                        features.saturn_square_moon = 1

            # Mars sextile Sun is energizing
            if planet == "Mars" and aspect_type == "sextile":
                features.mars_sextile_sun = 1

        features.benefic_aspects = min(benefic_count, 5)  # Cap at 5
        features.malefic_aspects = min(malefic_count, 5)

        # 3. Transit state counts (normalized)
        features.retrograde_count = transits.get("retrograde_count", 0) / 9.0
        features.exalted_count = len(transits.get("exalted_planets", [])) / 3.0
        features.debilitated_count = len(transits.get("debilitated_planets", [])) / 3.0

        # 4. Dignity scores
        current = transits.get("current_positions", {})

        for planet in ["Jupiter", "Saturn", "Venus"]:
            if planet in current:
                pos = current[planet]
                dignity = 0.0
                if pos.get("exalted"):
                    dignity = 1.0
                elif pos.get("debilitated"):
                    dignity = -1.0
                setattr(features, f"{planet.lower()}_dignity", dignity)

        # 5. Gann Square of 9
        if current_price > 0:
            root = np.sqrt(current_price)
            features.price_angle = (root - int(root)) * 360.0 / 360.0
            # Cardinal points: 0°, 90°, 180°, 270°
            angle_deg = features.price_angle * 360
            features.price_at_cardinal = (
                1 if any(abs(angle_deg - cardinal) < 5 for cardinal in [0, 90, 180, 270]) else 0
            )

        # 6. Tattva integration
        features.tattva_coherence = tattva_state.get("coherence", 0.5)

        gunas = tattva_state.get("gunas", {})
        sattva = gunas.get("sattva", 0.33)
        rajas = gunas.get("rajas", 0.33)
        tamas = gunas.get("tamas", 0.33)

        if sattva > max(rajas, tamas):
            features.dominant_guna = 0
        elif rajas > tamas:
            features.dominant_guna = 1
        else:
            features.dominant_guna = 2

        # 7. Technical integration
        if technical_indicators:
            features.volatility_regime = technical_indicators.get("volatility", 0.5)
            features.trend_strength = technical_indicators.get("trend", 0.0)

        # 8. Composite astro scores
        features.astro_bullish_score = self._calculate_bullish_score(features, transits)
        features.astro_bearish_score = self._calculate_bearish_score(features, transits)

        # Convert to numpy array
        feature_vector = np.array(
            [
                features.sun_moon_angle,
                features.sun_jupiter_angle,
                features.moon_saturn_angle,
                features.mars_jupiter_angle,
                features.jupiter_trine_sun,
                features.saturn_square_moon,
                features.venus_trine_jupiter,
                features.mars_sextile_sun,
                features.benefic_aspects / 5.0,  # Normalize
                features.malefic_aspects / 5.0,
                features.retrograde_count,
                features.exalted_count,
                features.debilitated_count,
                (features.jupiter_dignity + 1) / 2,  # Normalize -1,1 to 0,1
                (features.saturn_dignity + 1) / 2,
                (features.venus_dignity + 1) / 2,
                features.price_at_cardinal,
                features.price_angle,
                features.tattva_coherence,
                features.dominant_guna / 2.0,  # 0,1,2 to 0,0.5,1
                features.volatility_regime,
                (features.trend_strength + 1) / 2,  # Normalize
                features.astro_bullish_score,
                features.astro_bearish_score,
            ],
            dtype=np.float32,
        )

        return feature_vector

    def _calculate_angle(self, planet1: dict, planet2: dict) -> float:
        """Calculate angle between two planets."""
        lon1 = planet1.get("longitude", 0)
        lon2 = planet2.get("longitude", 0)
        return abs(lon1 - lon2) % 360.0

    def _calculate_bullish_score(self, features: AstroFeatures, transits: dict) -> float:
        """
        Calculate composite bullish astrological score.

        Factors:
        - Jupiter/Venus exalted or well-aspected
        - Benefic aspects > malefic
        - High coherence
        - Sattva dominant
        """
        score = 0.5  # Neutral baseline

        # Jupiter dignity (strongest bullish indicator)
        score += features.jupiter_dignity * 0.2

        # Benefic aspects
        score += (features.benefic_aspects - features.malefic_aspects) * 0.05

        # Tattva alignment (Sattva = bullish)
        if features.dominant_guna == 0:
            score += 0.1

        # Coherence boost
        score += (features.tattva_coherence - 0.5) * 0.1

        # Exalted benefics
        exalted = transits.get("exalted_planets", [])
        if "Jupiter" in exalted:
            score += 0.1
        if "Venus" in exalted:
            score += 0.05

        return max(0.0, min(1.0, score))

    def _calculate_bearish_score(self, features: AstroFeatures, transits: dict) -> float:
        """
        Calculate composite bearish astrological score.

        Factors:
        - Saturn/Mars debilitated or afflicted
        - Malefic aspects > benefic
        - Low coherence
        - Tamas dominant
        - Many retrogrades
        """
        score = 0.5  # Neutral baseline

        # Saturn dignity (strongest bearish indicator when weak)
        score -= features.saturn_dignity * 0.15

        # Malefic aspects
        score += (features.malefic_aspects - features.benefic_aspects) * 0.05

        # Tattva alignment (Tamas = bearish)
        if features.dominant_guna == 2:
            score += 0.15

        # Low coherence
        score += (0.5 - features.tattva_coherence) * 0.1

        # Retrograde stress
        score += features.retrograde_count * 0.05

        # Debilitated malefics
        debilitated = transits.get("debilitated_planets", [])
        if "Saturn" in debilitated:
            score += 0.1
        if "Mars" in debilitated:
            score += 0.05

        return max(0.0, min(1.0, score))

    def get_feature_names(self) -> list[str]:
        """Get list of feature names."""
        return self.FEATURE_NAMES.copy()

    def explain_features(self, feature_vector: np.ndarray) -> dict[str, float]:
        """Create human-readable feature explanation."""
        return {
            name: float(value)
            for name, value in zip(self.FEATURE_NAMES, feature_vector, strict=False)
        }
