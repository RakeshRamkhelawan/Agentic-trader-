"""
A/B Testing Framework for Triad System

Compares Triad decisions against baseline strategies.
"""

import json
import logging
import statistics
from datetime import datetime
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class V17BaselineStrategy:
    """Baseline strategy based on V17 elemental harmony."""

    def __init__(self):
        self.name = "v17_baseline"

    def decide(self, market_data: dict) -> dict:
        if 'elemental_harmony' in market_data:
            harmony = market_data['elemental_harmony']
        elif 'rsi' in market_data:
            rsi = market_data['rsi']
            harmony = (rsi - 30) / 40
            harmony = max(0, min(1, harmony))
        else:
            harmony = 0.5

        if harmony > 0.6:
            return {"action": "buy", "confidence": harmony, "strategy": "v17"}
        elif harmony < 0.4:
            return {"action": "sell", "confidence": 1 - harmony, "strategy": "v17"}
        else:
            return {"action": "hold", "confidence": 0.5, "strategy": "v17"}


class RandomBaselineStrategy:
    """Random baseline for comparison."""

    def __init__(self, seed: int = 42):
        self.name = "random_baseline"
        self.rng = np.random.RandomState(seed)

    def decide(self, market_data: dict) -> dict:
        actions = ["buy", "sell", "hold"]
        action = self.rng.choice(actions)
        confidence = self.rng.uniform(0.5, 0.8)
        return {"action": action, "confidence": confidence, "strategy": "random"}


class BuyHoldStrategy:
    """Buy and hold baseline."""

    def __init__(self):
        self.name = "buy_hold"
        self.first_trade = True

    def decide(self, market_data: dict) -> dict:
        if self.first_trade:
            self.first_trade = False
            return {"action": "buy", "confidence": 1.0, "strategy": "buy_hold"}
        return {"action": "hold", "confidence": 1.0, "strategy": "buy_hold"}


class ABTestingFramework:
    """A/B Testing Framework for comparing Triad vs baselines."""

    def __init__(self, storage_path: str = "data/ab_testing"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.experiments: dict[str, dict] = {}
        self.baselines = {
            "v17": V17BaselineStrategy(),
            "random": RandomBaselineStrategy(),
            "buy_hold": BuyHoldStrategy()
        }
        self._load_experiments()
        logger.info("A/B Testing Framework initialized")

    def _load_experiments(self):
        exp_file = self.storage_path / "experiments.json"
        if exp_file.exists():
            try:
                with open(exp_file) as f:
                    self.experiments = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load: {e}")

    def _save_experiments(self):
        exp_file = self.storage_path / "experiments.json"
        with open(exp_file, 'w') as f:
            json.dump(self.experiments, f, indent=2, default=str)

    def start_experiment(self, experiment_id: str, baseline: str = "v17") -> dict:
        """Start new A/B test experiment."""
        if baseline not in self.baselines:
            raise ValueError(f"Unknown baseline: {baseline}")

        experiment = {
            "id": experiment_id,
            "baseline": baseline,
            "start_time": datetime.utcnow().isoformat(),
            "status": "running",
            "triad_results": [],
            "baseline_results": []
        }

        self.experiments[experiment_id] = experiment
        self._save_experiments()
        logger.info(f"Started experiment {experiment_id} vs {baseline}")
        return experiment

    def get_baseline_decision(self, experiment_id: str, market_data: dict) -> dict:
        """Get baseline decision for experiment."""
        baseline_name = self.experiments[experiment_id]["baseline"]
        return self.baselines[baseline_name].decide(market_data)

    def record_outcome(self, experiment_id: str, variant: str, pnl: float):
        """Record trade outcome."""
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "pnl": pnl
        }
        self.experiments[experiment_id][f"{variant}_results"].append(result)
        self._save_experiments()

    def end_experiment(self, experiment_id: str) -> dict:
        """End experiment and calculate results."""
        exp = self.experiments[experiment_id]
        exp["status"] = "completed"
        exp["end_time"] = datetime.utcnow().isoformat()

        triad_pnls = [r["pnl"] for r in exp["triad_results"]]
        baseline_pnls = [r["pnl"] for r in exp["baseline_results"]]

        analysis = {
            "triad": self._calc_stats(triad_pnls),
            "baseline": self._calc_stats(baseline_pnls),
            "comparison": self._compare(triad_pnls, baseline_pnls)
        }

        exp["analysis"] = analysis
        self._save_experiments()
        return analysis

    def _calc_stats(self, pnls: list[float]) -> dict:
        if not pnls:
            return {"trades": 0, "win_rate": 0, "total_pnl": 0, "avg_pnl": 0}

        wins = sum(1 for p in pnls if p > 0)
        return {
            "trades": len(pnls),
            "win_rate": wins / len(pnls),
            "total_pnl": sum(pnls),
            "avg_pnl": statistics.mean(pnls)
        }

    def _compare(self, triad_pnls: list[float], baseline_pnls: list[float]) -> dict:
        if not triad_pnls or not baseline_pnls:
            return {"status": "insufficient_data"}

        triad_total = sum(triad_pnls)
        baseline_total = sum(baseline_pnls)

        return {
            "triad_pnl": triad_total,
            "baseline_pnl": baseline_total,
            "difference": triad_total - baseline_total,
            "winner": "triad" if triad_total > baseline_total else "baseline"
        }

    def get_report(self, experiment_id: str) -> str:
        """Generate experiment report."""
        exp = self.experiments[experiment_id]
        if "analysis" not in exp:
            return "Experiment not completed"

        a = exp["analysis"]
        return f"""
{'='*50}
A/B TEST REPORT: {experiment_id}
{'='*50}
Baseline: {exp['baseline']}

TRIAD:
  Trades: {a['triad']['trades']}
  Win Rate: {a['triad']['win_rate']:.1%}
  Total PnL: ${a['triad']['total_pnl']:,.2f}

BASELINE:
  Trades: {a['baseline']['trades']}
  Win Rate: {a['baseline']['win_rate']:.1%}
  Total PnL: ${a['baseline']['total_pnl']:,.2f}

COMPARISON:
  Difference: ${a['comparison']['difference']:,.2f}
  Winner: {a['comparison']['winner'].upper()}
{'='*50}
"""


_ab_framework = None


def get_ab_framework():
    global _ab_framework
    if _ab_framework is None:
        _ab_framework = ABTestingFramework()
    return _ab_framework


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 50)
    print("A/B TESTING FRAMEWORK - TEST")
    print("=" * 50)

    ab = get_ab_framework()

    # Start experiment
    exp = ab.start_experiment("test_001", baseline="random")
    print(f"Started: {exp['id']}")

    # Simulate trades
    import random
    for i in range(20):
        market = {"rsi": random.uniform(30, 70)}

        # Triad (better performance)
        triad_pnl = random.gauss(50, 80)
        ab.record_outcome("test_001", "triad", triad_pnl)

        # Random baseline
        baseline_pnl = random.gauss(10, 100)
        ab.record_outcome("test_001", "baseline", baseline_pnl)

    # End and report
    analysis = ab.end_experiment("test_001")
    print(ab.get_report("test_001"))
