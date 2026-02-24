"""
Backtest V18 Validator: Replay trades met V15 vs V18 consensus logica

Analyseert bestaande backtest data en simuleert welke trades
WEL zouden doorgaan onder V18 vs welke NIET.

Output: JSON met vergelijking + actionable insights
"""

import json
import sys
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class TradeAnalysis:
    """Analyse van een enkele trade."""
    timestamp: str
    symbol: str
    action: str
    price: float
    v15_passed: bool
    v18_passed: bool
    v18_regime: str
    v18_consensus: float
    v18_threshold: float
    dominant_agent: str
    earth_vote: float
    vedastro_vote: float
    fire_vote: float
    vayu_dampener: float
    pnl_pct: float = 0.0


class V18ConsensusSimulator:
    """Simuleert V18 consensus op basis van trade eigenschappen."""

    def __init__(self):
        self.price_histories = defaultdict(list)
        self.results = []

    def get_regime(self, symbol: str) -> str:
        """Detecteer regime obv price history."""
        prices = self.price_histories[symbol]
        if len(prices) < 20:
            return "neutral"

        recent = prices[-20:]
        returns = [(recent[i] - recent[i-1]) / recent[i-1] for i in range(1, len(recent))]
        avg_return = sum(returns) / len(returns)
        volatility = np.std(returns) if len(returns) > 1 else 0

        if avg_return > 0.002 and volatility < 0.02:
            return "expansion"
        elif avg_return < -0.002 or volatility > 0.04:
            return "contraction"
        return "neutral"

    def get_vayu_dampener(self, symbol: str) -> float:
        """Bereken Vayu dampener."""
        prices = self.price_histories[symbol]
        if len(prices) < 10:
            return 1.0

        recent = prices[-10:]
        returns = [(recent[i] - recent[i-1]) / recent[i-1] for i in range(1, len(recent))]
        avg_vol = sum(abs(r) for r in returns) / len(returns)

        if avg_vol > 0.05:
            return 0.7
        elif avg_vol > 0.03:
            return 0.85
        return 1.0

    def simulate_v15(self, symbol: str) -> Tuple[bool, float]:
        """Simuleer V15 (static) consensus."""
        prices = self.price_histories[symbol]
        if len(prices) < 5:
            return True, 0.45  # Default: pass (originele trade deed het ook)

        # Simuleer agent votes obv prijs momentum
        momentum = (prices[-1] - prices[-5]) / prices[-5]

        # VedAstro: positief bij stijgende trend
        vedastro = 0.6 if momentum > 0 else 0.3
        # Earth: positief bij lage volatiliteit
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(-4, 0)]
        vol = sum(abs(r) for r in returns) / len(returns) if returns else 0.02
        earth = 0.5 if vol < 0.03 else 0.2
        # Fire: positief bij groot momentum
        fire = min(0.8, max(0.2, abs(momentum) * 10))

        consensus = vedastro * 0.40 + earth * 0.30 + fire * 0.30
        return consensus >= 0.30, consensus

    def simulate_v18(self, symbol: str) -> Tuple[bool, float, str, Dict]:
        """Simuleer V18 (dynamic) consensus."""
        prices = self.price_histories[symbol]
        if len(prices) < 5:
            # Niet genoeg data - default naar pass (originele trade)
            return True, 0.45, "neutral", {
                "vedastro_vote": 0.5, "earth_vote": 0.5, "fire_vote": 0.5,
                "water_vote": 0.3, "guna_multiplier": 1.0, "vayu_dampener": 1.0,
                "raw_consensus": 0.45, "threshold": 0.30, "dominant_agent": "EARTH"
            }

        regime = self.get_regime(symbol)
        vayu = self.get_vayu_dampener(symbol)

        # Gewichten per regime
        if regime == "expansion":
            weights = {"vedastro": 0.40, "earth": 0.25, "fire": 0.25, "water": 0.10}
            threshold = 0.30
        elif regime == "contraction":
            weights = {"vedastro": 0.20, "earth": 0.45, "fire": 0.15, "water": 0.20}
            threshold = 0.35
        else:
            weights = {"vedastro": 0.30, "earth": 0.30, "fire": 0.25, "water": 0.15}
            threshold = 0.30

        # Bereken votes
        momentum = (prices[-1] - prices[-5]) / prices[-5]
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(-4, 0)]
        vol = sum(abs(r) for r in returns) / len(returns) if returns else 0.02

        # Gunas multiplier
        direction_changes = sum(1 for i in range(1, len(returns)) if returns[i] * returns[i-1] < 0) if len(returns) > 1 else 0
        if vol < 0.01 and direction_changes <= 1:
            guna_mult = 1.1
        elif vol > 0.03 and direction_changes >= 2:
            guna_mult = 0.9
        else:
            guna_mult = 1.0

        vedastro = (0.6 if momentum > 0 else 0.3) * guna_mult
        earth = 0.5 if vol < 0.03 else 0.2
        fire = min(0.8, max(0.2, abs(momentum) * 10))
        water = 0.3

        raw_consensus = (
            vedastro * weights["vedastro"] +
            earth * weights["earth"] +
            fire * weights["fire"] +
            water * weights["water"]
        )

        total_consensus = raw_consensus * vayu
        effective_threshold = threshold * vayu

        weighted = {
            "VEDASTRO": vedastro * weights["vedastro"],
            "EARTH": earth * weights["earth"],
            "FIRE": fire * weights["fire"],
            "WATER": water * weights["water"],
        }
        dominant = max(weighted, key=weighted.get)

        details = {
            "vedastro_vote": vedastro,
            "earth_vote": earth,
            "fire_vote": fire,
            "water_vote": water,
            "guna_multiplier": guna_mult,
            "vayu_dampener": vayu,
            "raw_consensus": raw_consensus,
            "threshold": effective_threshold,
            "dominant_agent": dominant,
        }

        return total_consensus >= effective_threshold, total_consensus, regime, details

    def analyze_backtest(self, backtest_file: str) -> Dict[str, Any]:
        """Analyseer volledige backtest."""
        print(f"Loading backtest: {backtest_file}")

        with open(backtest_file, 'r') as f:
            data = json.load(f)

        trades = data.get('trades', [])
        print(f"Loaded {len(trades)} trades")
        print(f"Original return: {data.get('total_return_pct', 0):.2f}%")
        print(f"Original max drawdown: {data.get('max_drawdown_pct', 0):.2f}%")

        analyses = []

        for trade in trades:
            symbol = trade['symbol']
            price = trade['price']
            action = trade.get('action', 'buy')

            # Update price history
            self.price_histories[symbol].append(price)

            # Alleen entries analyseren (niet exits)
            if action != 'buy':
                continue

            # Simuleer beide configuraties
            v15_passed, v15_consensus = self.simulate_v15(symbol)
            v18_passed, v18_consensus, regime, details = self.simulate_v18(symbol)

            analysis = TradeAnalysis(
                timestamp=trade.get('timestamp', ''),
                symbol=symbol,
                action=action,
                price=price,
                v15_passed=v15_passed,
                v18_passed=v18_passed,
                v18_regime=regime,
                v18_consensus=v18_consensus,
                v18_threshold=details.get('threshold', 0.30),
                dominant_agent=details.get('dominant_agent', 'UNKNOWN'),
                earth_vote=details.get('earth_vote', 0),
                vedastro_vote=details.get('vedastro_vote', 0),
                fire_vote=details.get('fire_vote', 0),
                vayu_dampener=details.get('vayu_dampener', 1.0),
            )
            analyses.append(analysis)

        return self.generate_report(analyses, data)

    def generate_report(self, analyses: List[TradeAnalysis], original_data: Dict) -> Dict[str, Any]:
        """Genereer vergelijkingsrapport."""

        # Basis counts
        total_evaluations = len(analyses)
        v15_trades = sum(1 for a in analyses if a.v15_passed)
        v18_trades = sum(1 for a in analyses if a.v18_passed)

        # Regime distributie
        regime_counts = defaultdict(lambda: {'v15': 0, 'v18': 0, 'total': 0})
        for a in analyses:
            regime_counts[a.v18_regime]['total'] += 1
            if a.v15_passed:
                regime_counts[a.v18_regime]['v15'] += 1
            if a.v18_passed:
                regime_counts[a.v18_regime]['v18'] += 1

        # Dominant agent analyse
        agent_performance = defaultdict(lambda: {'trades': 0, 'total': 0})
        for a in analyses:
            agent_performance[a.dominant_agent]['total'] += 1
            if a.v18_passed:
                agent_performance[a.dominant_agent]['trades'] += 1

        # Vayu analyse
        vayu_events = sum(1 for a in analyses if a.vayu_dampener < 1.0)
        vayu_blocked = sum(1 for a in analyses if a.vayu_dampener < 1.0 and not a.v18_passed)

        # Verschillen
        v18_only = sum(1 for a in analyses if not a.v15_passed and a.v18_passed)
        v15_only = sum(1 for a in analyses if a.v15_passed and not a.v18_passed)
        both = sum(1 for a in analyses if a.v15_passed and a.v18_passed)
        neither = sum(1 for a in analyses if not a.v15_passed and not a.v18_passed)

        report = {
            "summary": {
                "total_evaluations": total_evaluations,
                "original_trades": original_data.get('total_trades', 0),
                "v15_trades": v15_trades,
                "v18_trades": v18_trades,
                "trade_reduction_pct": ((v15_trades - v18_trades) / v15_trades * 100) if v15_trades > 0 else 0,
                "vayu_dampening_events": vayu_events,
                "vayu_blocked_trades": vayu_blocked,
            },
            "overlap_analysis": {
                "both_configs": both,
                "v15_only": v15_only,
                "v18_only": v18_only,
                "neither": neither,
            },
            "regime_performance": {
                regime: {
                    "total_evaluations": counts['total'],
                    "v15_trades": counts['v15'],
                    "v18_trades": counts['v18'],
                    "v18_selectivity": (counts['v18'] / counts['total'] * 100) if counts['total'] > 0 else 0
                }
                for regime, counts in regime_counts.items()
            },
            "agent_performance": {
                agent: {
                    "total_evaluations": counts['total'],
                    "trades_led": counts['trades'],
                    "leadership_rate": (counts['trades'] / counts['total'] * 100) if counts['total'] > 0 else 0
                }
                for agent, counts in agent_performance.items()
            },
            "insights": self.generate_insights(analyses, v15_trades, v18_trades, regime_counts, agent_performance),
            "sample_trades": [asdict(a) for a in analyses[:10]]  # Eerste 10 als voorbeeld
        }

        return report

    def generate_insights(self, analyses: List[TradeAnalysis], v15_trades: int,
                         v18_trades: int, regime_counts: Dict, agent_perf: Dict) -> List[str]:
        """Genereer actionable insights."""
        insights = []

        # Trade selectiviteit
        reduction = ((v15_trades - v18_trades) / v15_trades * 100) if v15_trades > 0 else 0
        if reduction > 10:
            insights.append(f"[FILTER] V18 is {reduction:.1f}% selectiever dan V15 — minder trades, potentieel hogere kwaliteit")
        elif reduction < -10:
            insights.append(f"[WARNING] V18 doet {abs(reduction):.1f}% MEER trades — mogelijk overtrading")
        else:
            insights.append(f"[OK] Vergelijkbare activiteit: V18 doet {reduction:+.1f}% trades vs V15")

        # Regime analyse
        for regime, counts in regime_counts.items():
            if counts['total'] > 10:
                selectivity = (counts['v18'] / counts['total'] * 100) if counts['total'] > 0 else 0
                if regime == "contraction" and selectivity < 30:
                    insights.append(f"[DEFENSE] In {regime.upper()} regime is V18 conservatief ({selectivity:.1f}% trades) — goed voor kapitaalbescherming")
                elif regime == "expansion" and selectivity > 50:
                    insights.append(f"[OFFENSE] In {regime.upper()} regime is V18 agressief ({selectivity:.1f}% trades) — benut momentum")

        # Agent dominantie
        earth_rate = agent_perf.get('EARTH', {}).get('leadership_rate', 0)
        vedastro_rate = agent_perf.get('VEDASTRO', {}).get('leadership_rate', 0)

        if earth_rate > vedastro_rate:
            insights.append(f"[EARTH] EARTH leidt {earth_rate:.1f}% van trades vs VedAstro {vedastro_rate:.1f}% — risicomanagement domineert")
        else:
            insights.append(f"[VEDASTRO] VedAstro leidt {vedastro_rate:.1f}% van trades — timing is key factor")

        # Vayu impact
        vayu_events = sum(1 for a in analyses if a.vayu_dampener < 1.0)
        vayu_pct = (vayu_events / len(analyses) * 100) if analyses else 0
        if vayu_pct > 20:
            insights.append(f"[VAYU] Vayu dempte {vayu_pct:.1f}% van evaluaties — volatiliteitsfilter is actief")

        return insights


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Backtest V18 Validator")
    parser.add_argument("backtest_file", help="Path to backtest JSON")
    parser.add_argument("--output", "-o", default="backtest_results/v18_analysis.json",
                       help="Output JSON file")

    args = parser.parse_args()

    # Run analyse
    simulator = V18ConsensusSimulator()
    report = simulator.analyze_backtest(args.backtest_file)

    # Print summary
    print("\n" + "="*70)
    print("V18 vs V15 CONSENSUS ANALYSIS")
    print("="*70)

    summary = report['summary']
    print(f"\n[TRADE ACTIVITY]")
    print(f"   Total evaluations: {summary['total_evaluations']}")
    print(f"   V15 (static) trades: {summary['v15_trades']}")
    print(f"   V18 (dynamic) trades: {summary['v18_trades']}")
    print(f"   Change: {summary['trade_reduction_pct']:+.1f}%")

    print(f"\n[REGIME DISTRIBUTION]")
    for regime, data in report['regime_performance'].items():
        print(f"   {regime}: {data['total_evaluations']} evals, "
              f"V18: {data['v18_trades']} trades ({data['v18_selectivity']:.1f}%)")

    print(f"\n[AGENT LEADERSHIP]")
    for agent, data in report['agent_performance'].items():
        print(f"   {agent}: {data['leadership_rate']:.1f}% of trades "
              f"({data['trades_led']}/{data['total_evaluations']})")

    print(f"\n[VAYU DAMPENING]")
    print(f"   Events: {summary['vayu_dampening_events']}")
    print(f"   Trades blocked: {summary['vayu_blocked_trades']}")

    print(f"\n[KEY INSIGHTS]")
    for insight in report['insights']:
        print(f"   {insight}")

    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n[SUCCESS] Full report saved to: {output_path}")


if __name__ == "__main__":
    main()
