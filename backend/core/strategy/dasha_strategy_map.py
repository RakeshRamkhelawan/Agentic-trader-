from enum import Enum
from typing import List

from pydantic import BaseModel


class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    HEDGED = "hedged"


class TimeHorizon(str, Enum):
    SCALP = "scalp"  # Seconds/Minutes
    INTRADAY = "intraday"  # Hours
    SWING = "swing"  # Days
    POSITION = "position"  # Weeks/Months


class AssetPreference(str, Enum):
    VOLATILE = "volatile"  # Crypto, Tech, High Beta
    STABLE = "stable"  # Bluechips, Stablecoins
    MOMENTUM = "momentum"  # Trending assets
    VALUE = "value"  # Undervalued assets
    SPECULATIVE = "speculative"  # Low cap, high risk


class StrategyConfig(BaseModel):
    risk_profile: RiskProfile
    time_horizon: TimeHorizon
    asset_preference: List[AssetPreference]
    description: str


class DashaStrategyMap:
    """
    Maps Vedic Mahadasha (Major Period) and Antardasha (Sub-period)
    to concrete trading strategy parameters.
    """

    def __init__(self):
        # Map Planet Name (English) to primary characteristics
        self.planet_map = {
            "Sun": {
                "risk": RiskProfile.MODERATE,
                "horizon": TimeHorizon.SWING,
                "asset": [AssetPreference.STABLE, AssetPreference.MOMENTUM],
                "desc": "Authority, consistency, trend following.",
            },
            "Moon": {
                "risk": RiskProfile.MODERATE,
                "horizon": TimeHorizon.INTRADAY,
                "asset": [AssetPreference.VOLATILE, AssetPreference.MOMENTUM],
                "desc": "Fluctuation, cyclicality, short-term flows.",
            },
            "Mars": {
                "risk": RiskProfile.AGGRESSIVE,
                "horizon": TimeHorizon.SCALP,
                "asset": [AssetPreference.VOLATILE, AssetPreference.MOMENTUM],
                "desc": "Aggression, energy, breakout trading.",
            },
            "Mercury": {
                "risk": RiskProfile.AGGRESSIVE,
                "horizon": TimeHorizon.SCALP,  # High frequency
                "asset": [AssetPreference.VOLATILE, AssetPreference.SPECULATIVE],
                "desc": "Intellect, speed, arbitrage, data-driven.",
            },
            "Jupiter": {
                "risk": RiskProfile.CONSERVATIVE,
                "horizon": TimeHorizon.POSITION,
                "asset": [AssetPreference.STABLE, AssetPreference.VALUE],
                "desc": "Wisdom, expansion, long-term growth.",
            },
            "Venus": {
                "risk": RiskProfile.MODERATE,
                "horizon": TimeHorizon.SWING,
                "asset": [
                    AssetPreference.VALUE,
                    AssetPreference.MOMENTUM,
                ],  # Reversion?
                "desc": "Harmony, mean reversion, comfort.",
            },
            "Saturn": {
                "risk": RiskProfile.CONSERVATIVE,
                "horizon": TimeHorizon.POSITION,
                "asset": [AssetPreference.VALUE, AssetPreference.STABLE],
                "desc": "Discipline, restriction, slow accumulation.",
            },
            "Rahu": {
                "risk": RiskProfile.AGGRESSIVE,
                "horizon": TimeHorizon.INTRADAY,  # Erratic
                "asset": [AssetPreference.VOLATILE, AssetPreference.SPECULATIVE],
                "desc": "Obsession, unexpected gains/losses, innovation.",
            },
            "Ketu": {
                "risk": RiskProfile.HEDGED,
                "horizon": TimeHorizon.SWING,
                "asset": [AssetPreference.VALUE],  # Detachment
                "desc": "Liberation, detachment, confusing signals, sudden breaks.",
            },
        }

    def get_strategy_config(self, mahadasha: str, antardasha: str) -> StrategyConfig:
        """
        Derive strategy from Dasha periods.
        Logic:
        - Mahadasha sets the 'Climate' (Time Horizon, Asset Class).
        - Antardasha sets the 'Weather' (Risk Profile, specific tactics).
        """

        # Normalize names just in case
        maha = mahadasha.capitalize() if mahadasha else "Sun"
        antar = antardasha.capitalize() if antardasha else maha

        maha_props = self.planet_map.get(maha, self.planet_map["Sun"])
        antar_props = self.planet_map.get(antar, self.planet_map["Sun"])

        # Composite Logic

        # Risk: Antardasha has stronger immediate influence on risk appetite
        risk = antar_props["risk"]

        # Horizon: Mahadasha sets the broad phase, but Antardasha can shorten it
        # If Mahadasha is Long but Antardasha is Short -> Medium (Swing)
        if (
            maha_props["horizon"] == TimeHorizon.POSITION
            and antar_props["horizon"] == TimeHorizon.SCALP
        ):
            horizon = TimeHorizon.INTRADAY
        elif (
            maha_props["horizon"] == TimeHorizon.POSITION
            and antar_props["horizon"] == TimeHorizon.INTRADAY
        ):
            horizon = TimeHorizon.SWING
        else:
            horizon = maha_props["horizon"]

        # Assets: Combine preferences
        assets = list(set(maha_props["asset"] + antar_props["asset"]))

        description = f"Mahadasha ({maha}): {maha_props['desc']} | Antardasha ({antar}): {antar_props['desc']}"

        return StrategyConfig(
            risk_profile=risk,
            time_horizon=horizon,
            asset_preference=assets,
            description=description,
        )
