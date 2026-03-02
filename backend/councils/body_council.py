"""
Body Council - Execution Layer

Analyseert execution omstandigheden:
- Slippage (verschil tussen verwacht en werkelijk)
- Fees (trading kosten)
- Latency (uitvoeringstijd)
- Liquidity (marktdiepte)

Output: Execution quality score + risk assessment
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetrics:
    """Metrics voor execution quality."""
    expected_price: float
    actual_price: float
    slippage_bps: float  # Basis points (1 bps = 0.01%)
    fees_bps: float
    latency_ms: float
    liquidity_score: float  # 0-1

    def total_cost_bps(self) -> float:
        """Totale kosten in basis points."""
        return abs(self.slippage_bps) + self.fees_bps


class BodyCouncil:
    """
    Body Council evalueert execution mogelijkheden.

    Focus: Kan de trade veilig en efficiënt worden uitgevoerd?
    """

    def __init__(self):
        # Thresholds voor execution quality
        self.max_acceptable_slippage = 50  # 50 bps = 0.5%
        self.max_acceptable_latency = 1000  # 1000ms = 1s
        self.min_liquidity_score = 0.3  # 30% van normale liquiditeit

    def analyze_execution_environment(self, market_data: dict) -> dict:
        """
        Analyseer execution environment zonder daadwerkelijke trade.

        Args:
            market_data: Dict met execution-relevante data

        Returns:
            Dict met execution assessment
        """
        # Extract metrics
        spread = market_data.get("bid_ask_spread", 0.001)
        spread_bps = spread * 10000  # Convert to basis points

        depth = market_data.get("orderbook_depth", 100000)  # Default $100k
        volume_24h = market_data.get("volume_24h", 1000000)

        # Calculate liquidity score
        liquidity_score = self._calc_liquidity_score(depth, volume_24h)

        # Estimate slippage for typical trade size
        trade_size = market_data.get("trade_size_usd", 10000)
        estimated_slippage = self._estimate_slippage(trade_size, depth, spread)

        # Check for adverse conditions
        issues = []

        if spread_bps > 20:  # > 0.2% spread
            issues.append(f"Wide spread: {spread_bps:.0f} bps")

        if liquidity_score < self.min_liquidity_score:
            issues.append(f"Low liquidity: {liquidity_score:.0%}")

        if estimated_slippage > self.max_acceptable_slippage:
            issues.append(f"High estimated slippage: {estimated_slippage:.0f} bps")

        # Determine execution quality
        if not issues:
            quality = "excellent"
            confidence = 0.9
            perspective = "favorable"
        elif len(issues) == 1 and estimated_slippage < 30:
            quality = "acceptable"
            confidence = 0.7
            perspective = "caution"
        else:
            quality = "poor"
            confidence = 0.4
            perspective = "avoid"

        return {
            "council_type": "body",
            "perspective": perspective,
            "confidence": confidence,
            "execution_quality": quality,
            "metrics": {
                "spread_bps": round(spread_bps, 1),
                "estimated_slippage_bps": round(estimated_slippage, 1),
                "liquidity_score": round(liquidity_score, 2),
                "depth_usd": depth
            },
            "issues": issues,
            "key_insights": self._generate_insights(quality, issues, spread_bps)
        }

    def assess_trade_execution(self, execution: ExecutionMetrics) -> dict:
        """
        Beoordeel een daadwerkelijke trade execution.

        Args:
            execution: ExecutionMetrics object

        Returns:
            Dict met execution assessment
        """
        total_cost = execution.total_cost_bps()

        # Grade the execution
        if total_cost < 10:  # < 0.1%
            grade = "excellent"
        elif total_cost < 30:  # < 0.3%
            grade = "good"
        elif total_cost < 50:  # < 0.5%
            grade = "fair"
        else:
            grade = "poor"

        # Check for problems
        problems = []

        if execution.slippage_bps > 20:
            problems.append(f"Significant slippage: {execution.slippage_bps:.0f} bps")

        if execution.latency_ms > 500:
            problems.append(f"High latency: {execution.latency_ms:.0f}ms")

        if execution.liquidity_score < 0.5:
            problems.append("Insufficient liquidity")

        return {
            "grade": grade,
            "total_cost_bps": round(total_cost, 1),
            "breakdown": {
                "slippage": round(execution.slippage_bps, 1),
                "fees": round(execution.fees_bps, 1),
                "latency_ms": round(execution.latency_ms, 0)
            },
            "problems": problems,
            "acceptable": grade in ["excellent", "good"]
        }

    def _calc_liquidity_score(self, depth: float, volume_24h: float) -> float:
        """
        Bereken liquidity score (0-1).

        Based on orderbook depth vs typical trade size.
        """
        # Assume typical trade is $10k
        typical_trade = 10000

        if depth >= typical_trade * 10:  # 10x depth
            return 1.0
        elif depth >= typical_trade * 5:  # 5x depth
            return 0.8
        elif depth >= typical_trade * 2:  # 2x depth
            return 0.6
        elif depth >= typical_trade:  # 1x depth
            return 0.4
        else:
            return max(0.1, depth / typical_trade)

    def _estimate_slippage(self, trade_size: float, depth: float, spread: float) -> float:
        """
        Schat slippage in basis points.

        Simple model: slippage increases as trade size approaches depth.
        """
        if depth <= 0:
            return 100  # 1% max slippage

        # Slippage factor based on trade size relative to depth
        size_ratio = trade_size / depth

        # Base slippage from spread (half spread for market order)
        base_slippage = (spread / 2) * 10000  # Convert to bps

        # Additional slippage from market impact
        impact_slippage = size_ratio * 100  # 100 bps at 100% of depth

        return base_slippage + impact_slippage

    def _generate_insights(self, quality: str, issues: list, spread_bps: float) -> list:
        """Genereer menselijke insights."""
        insights = []

        if quality == "excellent":
            insights.append("Excellent execution conditions")
            if spread_bps < 10:
                insights.append("Tight spreads favorable for entry")
        elif quality == "acceptable":
            insights.append(f"Execution acceptable with {len(issues)} caution(s)")
            for issue in issues:
                insights.append(f"Note: {issue}")
        else:
            insights.append("Poor execution conditions - consider waiting")
            for issue in issues:
                insights.append(f"Warning: {issue}")

        return insights


# Singleton
body_council = None


def get_body_council():
    """Get singleton instance."""
    global body_council
    if body_council is None:
        body_council = BodyCouncil()
    return body_council


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("BODY COUNCIL - TEST")
    print("=" * 60)

    council = get_body_council()

    # Test scenarios
    scenarios = [
        ("Liquid market", {
            "bid_ask_spread": 0.0005,
            "orderbook_depth": 500000,
            "volume_24h": 50000000,
            "trade_size_usd": 10000
        }),
        ("Illiquid market", {
            "bid_ask_spread": 0.005,
            "orderbook_depth": 5000,
            "volume_24h": 100000,
            "trade_size_usd": 10000
        }),
        ("Wide spread", {
            "bid_ask_spread": 0.003,
            "orderbook_depth": 200000,
            "volume_24h": 2000000,
            "trade_size_usd": 10000
        }),
    ]

    for name, data in scenarios:
        print(f"\n{name}:")
        result = council.analyze_execution_environment(data)
        print(f"  Quality: {result['execution_quality']}")
        print(f"  Perspective: {result['perspective']} (conf: {result['confidence']:.2f})")
        print(f"  Est. slippage: {result['metrics']['estimated_slippage_bps']:.0f} bps")
        print(f"  Issues: {result['issues'] or 'None'}")
