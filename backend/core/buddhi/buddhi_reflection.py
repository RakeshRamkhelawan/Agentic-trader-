"""
Buddhi Reflection - Zelfreflectie systeem zonder lookahead bias.

Gebruikt risico-gecorrigeerde metrics (Sharpe proxy) over meerdere horizons
in plaats van 1-punt directionaliteit.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DecisionOutcome:
    """Uitkomst van een trading beslissing."""
    decision_id: str
    timestamp: datetime
    symbol: str
    action: str  # buy, sell, hold
    entry_price: float

    # Multi-horizon returns (geen lookahead bias - pas berekend na tijd verstreken)
    returns_5m: float | None = None
    returns_15m: float | None = None
    returns_1h: float | None = None
    returns_4h: float | None = None

    # Risk metrics
    max_adverse_excursion: float | None = None  # Max drawdown na entry
    max_favorable_excursion: float | None = None  # Max profit na entry

    # Sharpe proxy (return / vol)
    sharpe_1h: float | None = None

    def is_profitable(self, horizon: str = "1h") -> bool:
        """Check of beslissing profitabel was op gegeven horizon."""
        ret = getattr(self, f"returns_{horizon}", None)
        if ret is None:
            return False

        # Voor buy: positieve return = goed
        # Voor sell: negatieve return = goed (prijs daalde)
        if self.action == "buy":
            return ret > 0
        elif self.action == "sell":
            return ret < 0
        return True  # Hold is altijd 'goed' (geen risico genomen)


@dataclass
class CouncilPerformance:
    """Performance metrics voor een council."""
    council_type: str
    total_signals: int
    correct_signals: int
    accuracy: float
    avg_confidence: float
    sharpe_contribution: float  # Hoeveel draagt deze council bij aan totale Sharpe?

    # Gewicht wordt dynamisch aangepast gebaseerd op recente performance
    current_weight: float


class BuddhiReflection:
    """
    Periodieke reflectie op eerdere beslissingen.

    BELANGRIJK: Geen lookahead bias! We evalueren pas nadat de tijd werkelijk
    is verstreken, niet door 'toekomstige' prijzen te gebruiken bij besluitvorming.
    """

    def __init__(
        self,
        evaluation_horizons: list[str] = None,
        min_samples_for_update: int = 10
    ):
        self.evaluation_horizons = evaluation_horizons or ["5m", "15m", "1h", "4h"]
        self.min_samples = min_samples_for_update

        # Performance tracking per council
        self.council_performances: dict[str, CouncilPerformance] = {}

        # Pending decisions die nog niet gevalueerd kunnen worden
        self.pending_decisions: list[DecisionOutcome] = []

        # Completed evaluations
        self.evaluation_history: list[DecisionOutcome] = []

        logger.info(f"BuddhiReflection initialized with horizons: {self.evaluation_horizons}")

    async def register_decision(
        self,
        decision_id: str,
        timestamp: datetime,
        symbol: str,
        action: str,
        entry_price: float,
        council_views: dict[str, float]  # council -> confidence
    ):
        """
        Registreer een nieuwe beslissing voor toekomstige evaluatie.
        """
        outcome = DecisionOutcome(
            decision_id=decision_id,
            timestamp=timestamp,
            symbol=symbol,
            action=action,
            entry_price=entry_price
        )

        self.pending_decisions.append(outcome)

        # Log council participatie
        for council, confidence in council_views.items():
            if council not in self.council_performances:
                self.council_performances[council] = CouncilPerformance(
                    council_type=council,
                    total_signals=0,
                    correct_signals=0,
                    accuracy=0.5,
                    avg_confidence=0.5,
                    sharpe_contribution=0.0,
                    current_weight=1.0
                )

        logger.debug(f"Registered decision {decision_id} for future evaluation")

    async def evaluate_pending_decisions(
        self,
        price_fetcher,  # Async callable: fetch_price_at(symbol, timestamp)
        current_time: datetime | None = None
    ):
        """
        Evalueer pending decisions waarvan de horizons zijn verstreken.

        Deze functie wordt periodiek aangeroepen (bijv. elke 5 minuten).
        """
        if current_time is None:
            current_time = datetime.utcnow()

        completed = []

        for outcome in self.pending_decisions[:]:  # Copy om te kunnen muteren
            time_since = (current_time - outcome.timestamp).total_seconds()

            # Check welke horizons beschikbaar zijn
            horizon_minutes = {
                "5m": 5,
                "15m": 15,
                "1h": 60,
                "4h": 240
            }

            all_available = True
            returns = {}

            for horizon in self.evaluation_horizons:
                minutes = horizon_minutes.get(horizon, 60)

                if time_since >= minutes * 60:
                    # Fetch price op dit horizon punt
                    horizon_time = outcome.timestamp + timedelta(minutes=minutes)

                    try:
                        price = await price_fetcher(outcome.symbol, horizon_time)
                        if price and price > 0:
                            ret = (price - outcome.entry_price) / outcome.entry_price
                            returns[f"returns_{horizon}"] = ret
                        else:
                            all_available = False
                            break
                    except Exception as e:
                        logger.warning(f"Could not fetch price for {outcome.symbol} at {horizon_time}: {e}")
                        all_available = False
                        break
                else:
                    # Nog niet genoeg tijd verstreken voor deze horizon
                    all_available = False
                    break

            if all_available:
                # Alle returns beschikbaar, bereken metrics
                outcome.returns_5m = returns.get("returns_5m")
                outcome.returns_15m = returns.get("returns_15m")
                outcome.returns_1h = returns.get("returns_1h")
                outcome.returns_4h = returns.get("returns_4h")

                # Bereken Sharpe proxy (mean return / std dev)
                returns_list = [r for r in [outcome.returns_5m, outcome.returns_15m,
                                            outcome.returns_1h, outcome.returns_4h] if r is not None]
                if returns_list:
                    mean_ret = np.mean(returns_list)
                    std_ret = np.std(returns_list) + 1e-8  # Avoid div by zero
                    outcome.sharpe_1h = mean_ret / std_ret

                completed.append(outcome)
                self.pending_decisions.remove(outcome)
                self.evaluation_history.append(outcome)

        if completed:
            logger.info(f"Evaluated {len(completed)} decisions")
            await self._update_council_weights(completed)

        return len(completed)

    async def _update_council_weights(self, outcomes: list[DecisionOutcome]):
        """
        Update council weights gebaseerd op hun bijdrage aan correcte beslissingen.
        """
        if len(self.evaluation_history) < self.min_samples:
            logger.debug(f"Not enough samples ({len(self.evaluation_history)}) to update weights")
            return

        # Analyseer welke councils correct waren
        for perf in self.council_performances.values():
            # Filter outcomes waar deze council aan meedeed
            # (In praktijk zou je moeten tracken welke councils bij welke decision hoorden)

            # Simpele update: gebruik recente accuracy
            recent_outcomes = self.evaluation_history[-50:]  # Laatste 50

            # Bereken hoe vaak beslissingen met hoge confidence van deze council correct waren
            correct = sum(1 for o in recent_outcomes if o.is_profitable("1h"))
            total = len(recent_outcomes)

            if total > 0:
                perf.accuracy = correct / total

                # Update weight: councils met accuracy < 0.4 krijgen lager gewicht
                if perf.accuracy < 0.4:
                    perf.current_weight *= 0.95  # Penalize
                elif perf.accuracy > 0.6:
                    perf.current_weight *= 1.05  # Reward

                # Clamp weight
                perf.current_weight = max(0.5, min(2.0, perf.current_weight))

        logger.info("Updated council weights based on performance")

    def calculate_decision_quality(
        self,
        decision: DecisionOutcome,
        horizon: str = "1h"
    ) -> float:
        """
        Bereken kwaliteit van een beslissing gebruikmakend van Sharpe proxy.

        Dit is veel robuuster dan simpele directionaliteit.
        """
        ret = getattr(decision, f"returns_{horizon}", None)
        if ret is None:
            return 0.0

        # Voor sell decisions: flip the return
        if decision.action == "sell":
            ret = -ret
        elif decision.action == "hold":
            # Hold is goed als de markt later beweegt (we vermeden risico)
            # Maar slecht als we een grote move gemist hebben
            ret = abs(ret) * 0.1  # Kleine reward voor vermeden risico

        # Gebruik Sharpe als beschikbaar
        if decision.sharpe_1h:
            # Combineer return en Sharpe
            quality = (ret * 0.7) + (decision.sharpe_1h * 0.1)
        else:
            quality = ret

        return quality

    def get_council_weights(self) -> dict[str, float]:
        """Huidige gewichten voor council input."""
        return {
            name: perf.current_weight
            for name, perf in self.council_performances.items()
        }

    def get_performance_summary(self) -> dict:
        """Samenvatting van recente performance."""
        if not self.evaluation_history:
            return {"status": "insufficient_data"}

        recent = self.evaluation_history[-100:]

        profitable = sum(1 for o in recent if o.is_profitable("1h"))

        return {
            "total_evaluated": len(self.evaluation_history),
            "recent_evaluated": len(recent),
            "accuracy_1h": profitable / len(recent) if recent else 0,
            "avg_sharpe": np.mean([o.sharpe_1h for o in recent if o.sharpe_1h]),
            "council_weights": self.get_council_weights(),
            "pending_evaluations": len(self.pending_decisions)
        }
