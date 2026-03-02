"""
Dynamic Guna Council

Berekent Guna balans (Sattva/Rajas/Tamas) DYNAMISCH uit market data.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GunaVector:
    """Guna balans vector - som altijd 1.0"""

    sattva: float
    rajas: float
    tamas: float

    def dominant(self) -> str:
        values = {"sattva": self.sattva, "rajas": self.rajas, "tamas": self.tamas}
        return max(values, key=values.get)

    def to_dict(self) -> dict:
        return {
            "sattva": round(self.sattva, 3),
            "rajas": round(self.rajas, 3),
            "tamas": round(self.tamas, 3),
            "dominant": self.dominant(),
        }


class DynamicGunaCouncil:
    """
    Guna Council die marktcondities analyseert.
    """

    def __init__(self, calibration_data: dict | None = None):
        if calibration_data:
            self.normal_vol = calibration_data.get("normal_vol", 0.02)
            self.high_vol = calibration_data.get("high_vol", 0.035)
            self.high_volume = calibration_data.get("high_volume", 1.34)
        else:
            self.normal_vol = 0.02
            self.high_vol = 0.035
            self.high_volume = 1.34

    def analyze(self, market_data: dict) -> dict:
        """Analyseer marktdata en return Guna balans."""
        vol = market_data.get("volatility_1m", 0.02)
        momentum = abs(market_data.get("momentum_1d", 0))
        vol_ratio = market_data.get("volume_ratio", 1.0)
        spread = market_data.get("bid_ask_spread", 0.001)
        trend = market_data.get("trend", 0)

        # Calculate scores
        sattva_score = self._calc_sattva(vol, spread, vol_ratio)
        rajas_score = self._calc_rajas(vol, momentum, vol_ratio, trend)
        tamas_score = self._calc_tamas(vol, vol_ratio, spread, trend)

        # Normalize
        total = sattva_score + rajas_score + tamas_score
        if total == 0:
            guna = GunaVector(sattva=0.33, rajas=0.33, tamas=0.34)
        else:
            guna = GunaVector(
                sattva=sattva_score / total, rajas=rajas_score / total, tamas=tamas_score / total
            )

        perspective, confidence = self._get_perspective(guna, trend)

        return {
            "council_type": "guna",
            "guna_vector": guna.to_dict(),
            "perspective": perspective,
            "confidence": round(confidence, 3),
            "key_insights": self._generate_insights(guna, vol, momentum, vol_ratio),
            "raw_scores": {
                "sattva": round(sattva_score, 3),
                "rajas": round(rajas_score, 3),
                "tamas": round(tamas_score, 3),
            },
        }

    def _calc_sattva(self, vol: float, spread: float, vol_ratio: float) -> float:
        """Sattva = harmonie, balans."""
        if vol < self.normal_vol:
            vol_score = 1.0
        elif vol < self.high_vol:
            vol_score = 0.5
        else:
            vol_score = 0.0

        spread_score = max(0, 1.0 - (spread / 0.002))

        if 0.8 < vol_ratio < 1.5:
            vol_ratio_score = 1.0
        else:
            vol_ratio_score = 0.3

        return (vol_score * 0.5) + (spread_score * 0.3) + (vol_ratio_score * 0.2)

    def _calc_rajas(self, vol: float, momentum: float, vol_ratio: float, trend: int) -> float:
        """Rajas = activiteit, beweging."""
        if vol > self.high_vol:
            vol_score = 1.0
        elif vol > self.normal_vol:
            vol_score = 0.6
        else:
            vol_score = 0.1

        momentum_score = min(1.0, momentum * 20)

        if vol_ratio > self.high_volume:
            vol_ratio_score = 1.0
        elif vol_ratio > 1.1:
            vol_ratio_score = 0.5
        else:
            vol_ratio_score = 0.0

        trend_score = 1.0 if trend != 0 else 0.2

        return (
            (vol_score * 0.3)
            + (momentum_score * 0.3)
            + (vol_ratio_score * 0.2)
            + (trend_score * 0.2)
        )

    def _calc_tamas(self, vol: float, vol_ratio: float, spread: float, trend: int) -> float:
        """Tamas = inertie, stagnatie."""
        if vol_ratio < 0.5:
            vol_ratio_score = 1.0
        elif vol_ratio < 0.8:
            vol_ratio_score = 0.5
        else:
            vol_ratio_score = 0.0

        trend_score = 1.0 if trend == 0 else 0.1

        if spread > 0.002 and vol < self.normal_vol:
            illiquid_score = 1.0
        else:
            illiquid_score = 0.0

        if vol < self.normal_vol * 0.5:
            low_vol_score = 0.8
        else:
            low_vol_score = 0.0

        return (
            (vol_ratio_score * 0.4)
            + (trend_score * 0.3)
            + (illiquid_score * 0.2)
            + (low_vol_score * 0.1)
        )

    def _get_perspective(self, guna: GunaVector, trend: int) -> tuple:
        """Bepaal trading perspective."""
        dominant = guna.dominant()

        if dominant == "rajas":
            if trend > 0:
                return "bullish", guna.rajas
            elif trend < 0:
                return "bearish", guna.rajas
            else:
                return "neutral", guna.rajas * 0.6
        elif dominant == "tamas":
            return "neutral", 1 - guna.tamas
        else:
            return "neutral", guna.sattva

    def _generate_insights(
        self, guna: GunaVector, vol: float, momentum: float, vol_ratio: float
    ) -> list:
        """Genereer insights."""
        insights = []
        dominant = guna.dominant()

        if dominant == "sattva":
            insights.append(f"Sattva {guna.sattva:.0%}: Harmonious conditions")
            if vol < self.normal_vol:
                insights.append(f"Low volatility ({vol:.2%}) suggests consolidation")
        elif dominant == "rajas":
            insights.append(f"Rajas {guna.rajas:.0%}: Active market")
            if momentum > 0.02:
                insights.append(f"Strong momentum ({momentum:+.1%})")
        else:
            insights.append(f"Tamas {guna.tamas:.0%}: Market inertia")
            if vol_ratio < 0.7:
                insights.append(f"Low volume ({vol_ratio:.1f}x) suggests indecision")

        return insights


# Singleton
guna_council = None


def get_guna_council():
    global guna_council
    if guna_council is None:
        try:
            from backend.core.market_data.calibrated_thresholds import get_thresholds

            cal = get_thresholds()
            thresholds = cal.get_thresholds()
            calibration = {
                "normal_vol": thresholds.get("normal_vol", 0.02),
                "high_vol": thresholds.get("euphoria_vol", 0.035),
                "high_volume": thresholds.get("high_volume", 1.34),
            }
            guna_council = DynamicGunaCouncil(calibration)
        except Exception:
            guna_council = DynamicGunaCouncil()
    return guna_council


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("DYNAMIC GUNA COUNCIL - TEST")
    print("=" * 60)

    council = get_guna_council()

    scenarios = [
        (
            "Calm consolidation",
            {
                "volatility_1m": 0.015,
                "momentum_1d": 0.005,
                "volume_ratio": 0.9,
                "bid_ask_spread": 0.0005,
                "trend": 0,
            },
        ),
        (
            "Strong uptrend",
            {
                "volatility_1m": 0.04,
                "momentum_1d": 0.035,
                "volume_ratio": 1.8,
                "bid_ask_spread": 0.001,
                "trend": 1,
            },
        ),
        (
            "Crash",
            {
                "volatility_1m": 0.08,
                "momentum_1d": -0.05,
                "volume_ratio": 2.5,
                "bid_ask_spread": 0.003,
                "trend": -1,
            },
        ),
    ]

    for name, data in scenarios:
        print(f"\n{name}:")
        result = council.analyze(data)
        guna = result["guna_vector"]
        print(f"  Guna: S={guna['sattva']}, R={guna['rajas']}, T={guna['tamas']}")
        print(f"  Dominant: {guna['dominant']}")
        print(f"  Perspective: {result['perspective']} (conf: {result['confidence']:.2f})")
