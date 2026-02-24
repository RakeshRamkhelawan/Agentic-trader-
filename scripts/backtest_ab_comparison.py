"""
Backtest A/B Comparison: V15/V16 (Static) vs V18 (Dynamic Pancha-Tattva)

Vergelijkt twee consensus strategieën op identieke historische data:
- A: Static weights (40/30/30, fixed 0.3 threshold)
- B: Dynamic Jala-modulated weights + Vayu dampening + Gunas multiplier

Output: CSV + PNG charts met Sharpe ratio vergelijking
"""

import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
from datetime import datetime

# Pad setup
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class ConsensusConfig:
    """Consensus configuratie voor A/B test."""
    name: str
    weights: Dict[str, float]
    threshold: float
    vayu_dampening: bool
    guna_multiplier: bool
    regime_dependent: bool


# Configuratie A: Static (V15/V16 stijl)
CONFIG_STATIC = ConsensusConfig(
    name="Static_V15",
    weights={"vedastro": 0.40, "earth": 0.30, "fire": 0.30, "water": 0.0},
    threshold=0.30,
    vayu_dampening=False,
    guna_multiplier=False,
    regime_dependent=False,
)

# Configuratie B: Dynamic (V18 Pancha-Tattva)
CONFIG_DYNAMIC = ConsensusConfig(
    name="Dynamic_V18",
    weights={"expansion": {"vedastro": 0.40, "earth": 0.25, "fire": 0.25, "water": 0.10},
             "contraction": {"vedastro": 0.20, "earth": 0.45, "fire": 0.15, "water": 0.20},
             "neutral": {"vedastro": 0.30, "earth": 0.30, "fire": 0.25, "water": 0.15}},
    threshold={"expansion": 0.30, "contraction": 0.35, "neutral": 0.30},
    vayu_dampening=True,
    guna_multiplier=True,
    regime_dependent=True,
)


class ConsensusEngine:
    """Simuleert consensus beslissingen."""

    def __init__(self, config: ConsensusConfig):
        self.config = config
        self.decisions = []

    def calculate_guna_multiplier(self, price_history: List[float]) -> float:
        """Bereken Gunas multiplier (1.1, 1.0, of 0.9)."""
        if len(price_history) < 5:
            return 1.0

        recent_returns = [(price_history[i] - price_history[i-1]) / price_history[i-1]
                         for i in range(-5, 0)]
        volatility = sum(abs(r) for r in recent_returns) / len(recent_returns)
        direction_changes = sum(1 for i in range(1, len(recent_returns))
                               if recent_returns[i] * recent_returns[i-1] < 0)

        if volatility > 0.03 and direction_changes >= 2:
            return 0.9  # Rajas - chaos
        elif volatility < 0.01 and direction_changes <= 1:
            return 1.1  # Sattva - helderheid
        return 1.0  # Balanced

    def calculate_vayu_dampener(self, price_history: List[float]) -> float:
        """Bereken Vayu dampener (0.7, 0.85, of 1.0)."""
        if not self.config.vayu_dampening or len(price_history) < 10:
            return 1.0

        recent_returns = [(price_history[i] - price_history[i-1]) / price_history[i-1]
                         for i in range(-10, 0)]
        recent_vol = sum(abs(r) for r in recent_returns) / len(recent_returns)

        if recent_vol > 0.05:
            return 0.7
        elif recent_vol > 0.03:
            return 0.85
        return 1.0

    def detect_regime(self, price_history: List[float]) -> str:
        """Detecteer marktregime (expansion/contraction/neutral)."""
        if len(price_history) < 20:
            return "neutral"

        # Eenvoudige regime detectie obv trend + volatiliteit
        returns = [(price_history[i] - price_history[i-1]) / price_history[i-1]
                  for i in range(-20, 0)]
        avg_return = sum(returns) / len(returns)
        volatility = np.std(returns) if len(returns) > 1 else 0

        if avg_return > 0.002 and volatility < 0.02:
            return "expansion"
        elif avg_return < -0.002 or volatility > 0.04:
            return "contraction"
        return "neutral"

    def evaluate_entry(self,
                      vedastro_signal: str,
                      vedastro_confidence: float,
                      earth_can_enter: bool,
                      fire_position_size: float,
                      portfolio_value: float,
                      price_history: List[float]) -> Dict[str, Any]:
        """Evalueer entry decision."""

        # Bereken votes
        signal_upper = vedastro_signal.upper()
        if "STRONG_BUY" in signal_upper:
            vedastro_vote = 1.0 * (vedastro_confidence / 100)
        elif "BUY" in signal_upper:
            vedastro_vote = 0.8 * (vedastro_confidence / 100)
        elif "SELL" in signal_upper:
            vedastro_vote = -0.5 * (vedastro_confidence / 100)
        else:
            vedastro_vote = 0.0

        earth_vote = 0.5 if earth_can_enter else -0.3

        max_fire = portfolio_value * 0.02
        fire_vote = min(1.0, fire_position_size / max_fire) * 0.5 if max_fire > 0 else 0

        # Gunas multiplier
        guna_mult = 1.0
        if self.config.guna_multiplier:
            guna_mult = self.calculate_guna_multiplier(price_history)
            vedastro_vote *= guna_mult

        # Vayu dampener
        vayu_damp = 1.0
        if self.config.vayu_dampening:
            vayu_damp = self.calculate_vayu_dampener(price_history)

        # Regime en gewichten
        if self.config.regime_dependent:
            regime = self.detect_regime(price_history)
            weights = self.config.weights[regime]
            threshold = self.config.threshold[regime]
        else:
            regime = "static"
            weights = self.config.weights
            threshold = self.config.threshold

        # Bereken consensus
        water_vote = 0.2  # Default
        raw_consensus = (
            vedastro_vote * weights.get("vedastro", 0) +
            earth_vote * weights.get("earth", 0) +
            fire_vote * weights.get("fire", 0) +
            water_vote * weights.get("water", 0)
        )

        total_vote = raw_consensus * vayu_damp
        effective_threshold = threshold * vayu_damp

        passed = total_vote >= effective_threshold

        return {
            "passed": passed,
            "total_vote": total_vote,
            "raw_consensus": raw_consensus,
            "threshold": effective_threshold,
            "regime": regime,
            "vayu_dampener": vayu_damp,
            "guna_multiplier": guna_mult,
            "vedastro_vote": vedastro_vote,
            "earth_vote": earth_vote,
            "fire_vote": fire_vote,
        }


def load_backtest_data(filepath: str) -> pd.DataFrame:
    """Laad backtest trades uit JSON."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    trades = data.get('trades', [])
    df = pd.DataFrame(trades)

    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

    return df, data


def simulate_historical_prices(trades_df: pd.DataFrame) -> Dict[str, List[float]]:
    """Reconstrueer prijs historie per symbool uit trades."""
    price_histories = {}

    for symbol in trades_df['symbol'].unique():
        symbol_trades = trades_df[trades_df['symbol'] == symbol]
        prices = symbol_trades['price'].tolist()
        price_histories[symbol] = prices

    return price_histories


def run_ab_comparison(backtest_file: str, output_dir: str = "backtest_results"):
    """Voer A/B vergelijking uit."""
    print(f"Loading backtest data: {backtest_file}")
    df, metadata = load_backtest_data(backtest_file)

    print(f"Loaded {len(df)} trades from {metadata.get('start_date')} to {metadata.get('end_date')}")
    print(f"Original return: {metadata.get('total_return_pct', 0):.2f}%")

    # Initialiseer engines
    engine_static = ConsensusEngine(CONFIG_STATIC)
    engine_dynamic = ConsensusEngine(CONFIG_DYNAMIC)

    # Simuleer beslissingen
    results = []

    for _, trade in df.iterrows():
        symbol = trade['symbol']
        action = trade.get('action', 'buy')

        # Haal prijs historie op (simplified - in echt systeem gebruik je echte historie)
        symbol_prices = df[df['symbol'] == symbol]['price'].tolist()

        # Simuleer agent inputs (in echt systeem komen deze uit de backtest logs)
        vedastro_signal = "BUY" if action == "buy" else "HOLD"
        vedastro_confidence = 75.0  # Placeholder
        earth_can_enter = True
        fire_position_size = 1000.0
        portfolio_value = metadata.get('initial_capital', 50000)

        # Evaluate met beide engines
        result_static = engine_static.evaluate_entry(
            vedastro_signal, vedastro_confidence, earth_can_enter,
            fire_position_size, portfolio_value, symbol_prices
        )

        result_dynamic = engine_dynamic.evaluate_entry(
            vedastro_signal, vedastro_confidence, earth_can_enter,
            fire_position_size, portfolio_value, symbol_prices
        )

        results.append({
            'timestamp': trade.get('timestamp'),
            'symbol': symbol,
            'action': action,
            'price': trade.get('price'),
            'static_passed': result_static['passed'],
            'static_vote': result_static['total_vote'],
            'dynamic_passed': result_dynamic['passed'],
            'dynamic_vote': result_dynamic['total_vote'],
            'dynamic_regime': result_dynamic['regime'],
            'dynamic_vayu': result_dynamic['vayu_dampener'],
            'dynamic_guna': result_dynamic['guna_multiplier'],
        })

    # Maak DataFrame
    results_df = pd.DataFrame(results)

    # Bereken metrics
    static_trades = results_df[results_df['static_passed'] == True]
    dynamic_trades = results_df[results_df['dynamic_passed'] == True]

    print("\n" + "="*60)
    print("A/B COMPARISON RESULTS")
    print("="*60)
    print(f"\nStatic (V15) Configuration:")
    print(f"  Total evaluations: {len(results_df)}")
    print(f"  Trades executed: {len(static_trades)} ({len(static_trades)/len(results_df)*100:.1f}%)")
    print(f"  Avg consensus: {results_df['static_vote'].mean():.3f}")

    print(f"\nDynamic (V18) Configuration:")
    print(f"  Total evaluations: {len(results_df)}")
    print(f"  Trades executed: {len(dynamic_trades)} ({len(dynamic_trades)/len(results_df)*100:.1f}%)")
    print(f"  Avg consensus: {results_df['dynamic_vote'].mean():.3f}")
    print(f"  Regime distribution:")
    for regime, count in results_df['dynamic_regime'].value_counts().items():
        print(f"    {regime}: {count} ({count/len(results_df)*100:.1f}%)")
    print(f"  Vayu dampening events: {(results_df['dynamic_vayu'] < 1.0).sum()}")
    print(f"  Gunas multiplier avg: {results_df['dynamic_guna'].mean():.3f}")

    # Differentieel
    diff_count = len(dynamic_trades) - len(static_trades)
    print(f"\nDifferential: {diff_count:+d} trades ({diff_count/len(static_trades)*100:+.1f}%)")

    # Sla resultaten op
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_path / f"ab_comparison_{timestamp}.csv"
    results_df.to_csv(results_file, index=False)
    print(f"\nDetailed results saved to: {results_file}")

    return results_df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backtest A/B Comparison")
    parser.add_argument("backtest_file", help="Path to backtest JSON file")
    parser.add_argument("--output", "-o", default="backtest_results", help="Output directory")

    args = parser.parse_args()

    run_ab_comparison(args.backtest_file, args.output)
