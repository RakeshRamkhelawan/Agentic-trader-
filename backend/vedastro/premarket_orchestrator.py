"""
VedAstro Pre-Market Orchestrator
================================

Fundamentele architectuur shift:
- OUD: VedAstro elke seconde aanroepen voor tactische besluiten
- NIEUW: 1x per dag pre-market analyse voor strategische planning

Workflow:
1. 08:00 UTC - Pre-Market Routine
   - Analyseer alle assets (compare_assets)
   - Rank op astrological strength score
   - Selecteer top 3-5 assets voor vandaag
   - Bepaal favorable trading hours (Pancha Pakshi)
   - Check Muhurtha dag rating

2. Trading Day - Execution Loop
   - Alleen traden tijdens favorable hours
   - Alleen in top-ranked assets
   - L2 agents (Guna, etc.) alleen actief in deze windows

3. End of Day - Review
   - Update performance metrics per asset
   - Cache leeren voor nieuwe dag

ADR-V001: Pancha Pakshi Trading Windows
---------------------------------------
Eating (1.0):  PRIME - Hoogste activiteit, beste voor entries
Ruling (0.9):  GOOD - Sterke controle, goed voor exits
Walking (0.7): MODERATE - Beweging, opletten
Sleeping (0.4): AVOID - Laag energie, geen nieuwe posities
Dying (0.1):   BLOCK - Zeer ongunstig, absoluut niet traden

ADR-V002: Asset Selection Criteria
----------------------------------
1. Astrological Score > 75/100
2. Muhurtha rating > 6/10
3. Geen Rikta Tithi
4. Gunstige Dasha periode (Mahadasha lord niet Saturn/Mars voor scalping)

ADR-V003: Time Window Management
--------------------------------
- Pre-market: Bereken alle timings voor de dag
- Active window: Start L2 agents alleen in favorable periods
- Cooldown: Force exit 15 min voor Sleeping/Dying periode
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .advanced_features import MuhurthaData, PanchaPakshiData
from .enhanced_orchestrator import CompleteAstroAnalysis, EnhancedAstroOrchestrator

logger = logging.getLogger(__name__)


class TradingWindow(Enum):
    """Pancha Pakshi trading window classifications"""

    PRIME = "prime"  # Eating - Best for entries
    GOOD = "good"  # Ruling - Good for exits
    MODERATE = "moderate"  # Walking - Cautious
    AVOID = "avoid"  # Sleeping - No new positions
    BLOCK = "block"  # Dying - Absolutely no trading


@dataclass
class AssetScore:
    """Astrological scoring for an asset"""

    symbol: str
    overall_score: float  # 0-100
    signal_strength: float  # 0-1
    confidence: float  # 0-1
    dasha_lord: str
    top_yoga: str
    muhurtha_rating: float  # 0-10
    pancha_pakshi_strength: float  # 0-1
    warnings: List[str] = field(default_factory=list)
    recommendation: str = "hold"


@dataclass
class TimeWindow:
    """Trading time window with VedAstro classification"""

    start_time: time
    end_time: time
    window_type: TradingWindow
    strength: float  # 0-1
    description: str
    recommended_action: str


@dataclass
class DailyTradingPlan:
    """Complete daily trading plan from VedAstro analysis"""

    date: str
    muhurtha_rating: float  # Overall day rating 0-10
    tithi: str
    tithi_type: str
    is_favorable_day: bool
    warnings: List[str]

    # Asset selection
    top_assets: List[AssetScore]  # Ranked list
    avoid_assets: List[str]  # Below threshold

    # Time windows
    trading_windows: List[TimeWindow]  # Favorable periods
    blocked_windows: List[TimeWindow]  # Unfavorable periods

    # Execution guidance
    best_entry_times: List[time]
    best_exit_times: List[time]
    max_positions: int
    risk_adjustment: float  # Multiplier based on day quality

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "date": self.date,
            "muhurtha_rating": self.muhurtha_rating,
            "tithi": self.tithi,
            "tithi_type": self.tithi_type,
            "is_favorable_day": self.is_favorable_day,
            "warnings": self.warnings,
            "top_assets": [asdict(a) for a in self.top_assets],
            "avoid_assets": self.avoid_assets,
            "trading_windows": [
                {
                    "start": w.start_time.isoformat(),
                    "end": w.end_time.isoformat(),
                    "type": w.window_type.value,
                    "strength": w.strength,
                    "description": w.description,
                    "action": w.recommended_action,
                }
                for w in self.trading_windows
            ],
            "blocked_windows": [
                {
                    "start": w.start_time.isoformat(),
                    "end": w.end_time.isoformat(),
                    "type": w.window_type.value,
                    "reason": w.description,
                }
                for w in self.blocked_windows
            ],
            "best_entry_times": [t.isoformat() for t in self.best_entry_times],
            "best_exit_times": [t.isoformat() for t in self.best_exit_times],
            "max_positions": self.max_positions,
            "risk_adjustment": self.risk_adjustment,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DailyTradingPlan":
        """Create from dictionary"""
        return cls(
            date=data["date"],
            muhurtha_rating=data["muhurtha_rating"],
            tithi=data["tithi"],
            tithi_type=data["tithi_type"],
            is_favorable_day=data["is_favorable_day"],
            warnings=data["warnings"],
            top_assets=[AssetScore(**a) for a in data["top_assets"]],
            avoid_assets=data["avoid_assets"],
            trading_windows=[
                TimeWindow(
                    start_time=datetime.fromisoformat(w["start"]).time(),
                    end_time=datetime.fromisoformat(w["end"]).time(),
                    window_type=TradingWindow(w["type"]),
                    strength=w["strength"],
                    description=w["description"],
                    recommended_action=w["action"],
                )
                for w in data["trading_windows"]
            ],
            blocked_windows=[
                TimeWindow(
                    start_time=datetime.fromisoformat(w["start"]).time(),
                    end_time=datetime.fromisoformat(w["end"]).time(),
                    window_type=TradingWindow(w["type"]),
                    strength=0.0,
                    description=w["reason"],
                    recommended_action="block",
                )
                for w in data["blocked_windows"]
            ],
            best_entry_times=[datetime.fromisoformat(t).time() for t in data["best_entry_times"]],
            best_exit_times=[datetime.fromisoformat(t).time() for t in data["best_exit_times"]],
            max_positions=data["max_positions"],
            risk_adjustment=data["risk_adjustment"],
        )


class VedAstroPreMarketOrchestrator:
    """
    Pre-Market VedAstro Orchestrator

    Runs once per day (08:00 UTC) to create complete trading plan.
    L2 agents consume this plan during trading hours.
    """

    # Configuration
    MIN_SCORE_THRESHOLD = 70  # Minimum score to include asset
    MIN_MUHURTHA_RATING = 6.0  # Minimum day rating
    MAX_TOP_ASSETS = 5  # Number of top assets to select

    # Time slots for analysis (24-hour day divided)
    TIME_SLOTS = [
        (time(0, 0), time(2, 24)),  # Night slot 1
        (time(2, 24), time(4, 48)),  # Night slot 2
        (time(4, 48), time(7, 12)),  # Dawn
        (time(7, 12), time(9, 36)),  # Morning
        (time(9, 36), time(12, 0)),  # Late morning
        (time(12, 0), time(14, 24)),  # Afternoon
        (time(14, 24), time(16, 48)),  # Late afternoon
        (time(16, 48), time(19, 12)),  # Evening
        (time(19, 12), time(21, 36)),  # Night slot 3
        (time(21, 36), time(0, 0)),  # Night slot 4
    ]

    def __init__(self):
        self.orchestrator = EnhancedAstroOrchestrator()
        self.daily_plan: Optional[DailyTradingPlan] = None
        self.plan_date: Optional[str] = None
        logger.info("VedAstro Pre-Market Orchestrator initialized")

    async def generate_daily_plan(
        self, symbols: List[str], analysis_date: Optional[datetime] = None
    ) -> DailyTradingPlan:
        """
        Generate complete daily trading plan

        Runs at 08:00 UTC pre-market
        """
        analysis_date = analysis_date or datetime.now()
        date_str = analysis_date.strftime("%Y-%m-%d")

        logger.info(f"Generating daily plan for {date_str} with {len(symbols)} assets")

        # 1. Analyze all assets
        asset_analyses = await self._analyze_all_assets(symbols, analysis_date)

        # 2. Score and rank assets
        asset_scores = self._score_assets(asset_analyses)

        # 3. Get Muhurtha for the day (from first asset)
        first_analysis = next(iter(asset_analyses.values()))
        muhurtha = first_analysis.muhurtha

        # 4. Calculate time windows for top asset
        top_asset = asset_scores[0].symbol if asset_scores else symbols[0]
        time_windows = self._calculate_time_windows(top_asset, analysis_date)

        # 5. Build trading plan
        plan = self._build_trading_plan(
            date=date_str, asset_scores=asset_scores, muhurtha=muhurtha, time_windows=time_windows
        )

        # Cache the plan
        self.daily_plan = plan
        self.plan_date = date_str

        # Save to file
        self._save_plan(plan)

        logger.info(
            f"Daily plan generated: {len(plan.top_assets)} top assets, "
            f"{len(plan.trading_windows)} trading windows"
        )

        return plan

    async def _analyze_all_assets(
        self, symbols: List[str], date: datetime
    ) -> Dict[str, CompleteAstroAnalysis]:
        """Analyze all assets for the day"""
        analyses = {}

        for symbol in symbols:
            try:
                analysis = await self.orchestrator.analyze_asset(symbol, current_date=date)
                analyses[symbol] = analysis
                logger.debug(f"Analyzed {symbol}: score={analysis.overall_score:.1f}")
            except Exception as e:
                logger.error(f"Failed to analyze {symbol}: {e}")

        return analyses

    def _score_assets(self, analyses: Dict[str, CompleteAstroAnalysis]) -> List[AssetScore]:
        """Score and rank all assets"""
        scores = []

        for symbol, analysis in analyses.items():
            score = AssetScore(
                symbol=symbol,
                overall_score=analysis.overall_score,
                signal_strength=analysis.trading_signal.strength_score,
                confidence=analysis.trading_signal.confidence,
                dasha_lord=analysis.dasha.mahadasha_lord if analysis.dasha else "Unknown",
                top_yoga=analysis.yogas[0].name if analysis.yogas else "None",
                muhurtha_rating=analysis.muhurtha.rating if analysis.muhurtha else 5.0,
                pancha_pakshi_strength=(
                    analysis.pancha_pakshi.strength if analysis.pancha_pakshi else 0.5
                ),
                warnings=analysis.muhurtha.warnings if analysis.muhurtha else [],
                recommendation=analysis.primary_recommendation,
            )
            scores.append(score)

        # Sort by overall score descending
        scores.sort(key=lambda x: x.overall_score, reverse=True)

        return scores

    def _calculate_time_windows(self, symbol: str, date: datetime) -> List[TimeWindow]:
        """Calculate Pancha Pakshi time windows for the day"""
        windows = []

        # Get analysis for each time slot
        for start, end in self.TIME_SLOTS:
            slot_time = datetime.combine(date.date(), start)

            # Get cached analysis or skip (should be cached from earlier)
            analysis = self._get_cached_analysis(symbol, slot_time)

            if analysis and analysis.pancha_pakshi:
                pp = analysis.pancha_pakshi
                window_type = self._classify_pancha_pakshi(pp.current_activity)

                window = TimeWindow(
                    start_time=start,
                    end_time=end,
                    window_type=window_type,
                    strength=pp.strength,
                    description=f"Pancha Pakshi: {pp.current_activity} (Bird: {pp.birth_bird})",
                    recommended_action=self._get_action_for_window(window_type),
                )
                windows.append(window)

        return windows

    def _classify_pancha_pakshi(self, activity: str) -> TradingWindow:
        """Classify Pancha Pakshi activity to trading window"""
        activity_map = {
            "eating": TradingWindow.PRIME,
            "ruling": TradingWindow.GOOD,
            "walking": TradingWindow.MODERATE,
            "sleeping": TradingWindow.AVOID,
            "dying": TradingWindow.BLOCK,
        }
        return activity_map.get(activity.lower(), TradingWindow.MODERATE)

    def _get_action_for_window(self, window: TradingWindow) -> str:
        """Get recommended action for trading window"""
        actions = {
            TradingWindow.PRIME: "Entry/Exit - Highest probability",
            TradingWindow.GOOD: "Exit/Trim - Controlled exit",
            TradingWindow.MODERATE: "Monitor only - No new positions",
            TradingWindow.AVOID: "No trading - Wait for better timing",
            TradingWindow.BLOCK: "ABSOLUTELY NO TRADING",
        }
        return actions.get(window, "Hold")

    def _build_trading_plan(
        self,
        date: str,
        asset_scores: List[AssetScore],
        muhurtha: Optional[MuhurthaData],
        time_windows: List[TimeWindow],
    ) -> DailyTradingPlan:
        """Build complete daily trading plan"""

        # Filter top assets
        top_assets = [a for a in asset_scores if a.overall_score >= self.MIN_SCORE_THRESHOLD]
        top_assets = top_assets[: self.MAX_TOP_ASSETS]

        # Assets to avoid
        avoid_assets = [
            a.symbol for a in asset_scores if a.overall_score < self.MIN_SCORE_THRESHOLD
        ]

        # Split windows
        trading_windows = [
            w
            for w in time_windows
            if w.window_type in [TradingWindow.PRIME, TradingWindow.GOOD, TradingWindow.MODERATE]
        ]
        blocked_windows = [
            w for w in time_windows if w.window_type in [TradingWindow.AVOID, TradingWindow.BLOCK]
        ]

        # Best entry/exit times
        best_entry_times = [
            w.start_time for w in time_windows if w.window_type == TradingWindow.PRIME
        ]
        best_exit_times = [
            w.start_time
            for w in time_windows
            if w.window_type in [TradingWindow.PRIME, TradingWindow.GOOD]
        ]

        # Risk adjustment based on day quality
        base_risk = 1.0
        if muhurtha:
            if muhurtha.rating >= 8:
                base_risk = 1.2  # Increase size on excellent days
            elif muhurtha.rating >= 6:
                base_risk = 1.0  # Normal
            elif muhurtha.rating >= 4:
                base_risk = 0.7  # Reduce size
            else:
                base_risk = 0.4  # Very cautious

        # Max positions based on day quality
        max_positions = 3 if (muhurtha and muhurtha.rating >= 7) else 2

        return DailyTradingPlan(
            date=date,
            muhurtha_rating=muhurtha.rating if muhurtha else 5.0,
            tithi=muhurtha.tithi if muhurtha else "Unknown",
            tithi_type=muhurtha.tithi_type if muhurtha else "Unknown",
            is_favorable_day=muhurtha.is_favorable if muhhurtha else False,
            warnings=muhurtha.warnings if muhhurtha else [],
            top_assets=top_assets,
            avoid_assets=avoid_assets,
            trading_windows=trading_windows,
            blocked_windows=blocked_windows,
            best_entry_times=best_entry_times,
            best_exit_times=best_exit_times,
            max_positions=max_positions,
            risk_adjustment=base_risk,
        )

    def _get_cached_analysis(self, symbol: str, time: datetime) -> Optional[CompleteAstroAnalysis]:
        """Get cached analysis if available"""
        cache_key = f"{symbol}:{time.strftime('%Y%m%d%H')}"
        return self.orchestrator._analysis_cache.get(cache_key)

    def _save_plan(self, plan: DailyTradingPlan):
        """Save plan to disk"""
        plan_dir = Path("data/trading_plans")
        plan_dir.mkdir(parents=True, exist_ok=True)

        plan_file = plan_dir / f"plan_{plan.date}.json"
        with open(plan_file, "w") as f:
            json.dump(plan.to_dict(), f, indent=2)

        logger.info(f"Trading plan saved to {plan_file}")

    def load_plan(self, date: str) -> Optional[DailyTradingPlan]:
        """Load plan from disk"""
        plan_file = Path(f"data/trading_plans/plan_{date}.json")

        if plan_file.exists():
            with open(plan_file, "r") as f:
                data = json.load(f)
                self.daily_plan = DailyTradingPlan.from_dict(data)
                self.plan_date = date
                return self.daily_plan

        return None

    def get_current_window(self, current_time: Optional[time] = None) -> Optional[TimeWindow]:
        """Get current trading window"""
        if not self.daily_plan:
            return None

        current_time = current_time or datetime.now().time()

        for window in self.daily_plan.trading_windows + self.daily_plan.blocked_windows:
            if window.start_time <= current_time < window.end_time:
                return window

        return None

    def can_trade_now(self, symbol: str, current_time: Optional[time] = None) -> Tuple[bool, str]:
        """Check if we can trade right now"""
        if not self.daily_plan:
            return False, "No daily plan available"

        current_time = current_time or datetime.now().time()

        # Check if in trading window
        window = self.get_current_window(current_time)
        if not window:
            return False, "Outside defined time windows"

        if window.window_type == TradingWindow.BLOCK:
            return False, f"BLOCKED: {window.description}"

        if window.window_type == TradingWindow.AVOID:
            return False, f"AVOID: {window.description}"

        # Check if symbol in top assets
        top_symbols = [a.symbol for a in self.daily_plan.top_assets]
        if symbol not in top_symbols:
            return False, f"{symbol} not in top assets today"

        return True, f"OK: {window.recommended_action} (strength: {window.strength:.2f})"

    def get_position_size_multiplier(self) -> float:
        """Get risk multiplier for current day"""
        if not self.daily_plan:
            return 1.0
        return self.daily_plan.risk_adjustment

    def is_favorable_day(self) -> bool:
        """Check if today is favorable for trading"""
        if not self.daily_plan:
            return False
        return (
            self.daily_plan.is_favorable_day
            and self.daily_plan.muhurtha_rating >= self.MIN_MUHURTHA_RATING
        )


# Convenience functions
async def generate_today_plan(symbols: List[str]) -> DailyTradingPlan:
    """Quick function to generate today's trading plan"""
    orchestrator = VedAstroPreMarketOrchestrator()
    return await orchestrator.generate_daily_plan(symbols)


def can_trade_symbol(
    symbol: str, plan: DailyTradingPlan, current_time: Optional[time] = None
) -> bool:
    """Check if symbol can be traded now based on plan"""
    current_time = current_time or datetime.now().time()

    # Check if in top assets
    top_symbols = [a.symbol for a in plan.top_assets]
    if symbol not in top_symbols:
        return False

    # Check if in favorable window
    for window in plan.trading_windows:
        if window.start_time <= current_time < window.end_time:
            if window.window_type in [TradingWindow.PRIME, TradingWindow.GOOD]:
                return True

    return False


# Example usage
if __name__ == "__main__":
    import asyncio

    async def demo():
        # Generate plan for today
        symbols = ["BTC", "ETH", "AAPL", "TSLA", "SPY"]
        plan = await generate_today_plan(symbols)

        print("\n" + "=" * 70)
        print(f"VEDASTRO TRADING PLAN - {plan.date}")
        print("=" * 70)
        print(
            f"\nDay Quality: {plan.muhurtha_rating:.1f}/10 - Tithi: {plan.tithi} ({plan.tithi_type})"
        )
        print(f"Favorable Day: {plan.is_favorable_day}")

        if plan.warnings:
            print("\nWarnings:")
            for w in plan.warnings:
                print(f"  ⚠ {w}")

        print("\nTop Assets:")
        for asset in plan.top_assets:
            print(f"  ✓ {asset.symbol}: {asset.overall_score:.1f}/100 - {asset.recommendation}")

        print("\nTrading Windows:")
        for window in plan.trading_windows:
            emoji = "🟢" if window.window_type == TradingWindow.PRIME else "🟡"
            print(
                f"  {emoji} {window.start_time.strftime('%H:%M')}-{window.end_time.strftime('%H:%M')}: "
                f"{window.description}"
            )

        print("\nBlocked Windows:")
        for window in plan.blocked_windows:
            print(
                f"  🔴 {window.start_time.strftime('%H:%M')}-{window.end_time.strftime('%H:%M')}: "
                f"{window.description}"
            )

        print("\n" + "=" * 70)

    asyncio.run(demo())
