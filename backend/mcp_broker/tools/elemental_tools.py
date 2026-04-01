"""
Elemental MCP Tools.

V17 Elemental Agents als stateless MCP tools.
Behoudt alle financiële constraints (€2k cap, 60-day failsafe, etc.)
"""

import logging
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import Context

from backend.mcp_broker.resilience import circuit_breaker, elemental_retry

logger = logging.getLogger(__name__)

# V17 Constants (BEHOUDEN!)
MAX_POSITION_EUR = 2000.0
MAX_HOLD_DAYS = 60
TRAILING_STOP_THRESHOLD = 0.40  # +40%
TRAILING_STOP_DISTANCE = 0.15  # -15% from peak

# Planet multipliers from V17
PLANET_RISK_MULTIPLIERS = {
    "SUN": 1.00,
    "MOON": 0.80,
    "MARS": 1.40,
    "MERCURY": 0.90,
    "JUPITER": 1.20,
    "VENUS": 1.10,
    "SATURN": 0.60,
    "RAHU": 0.70,
    "KETU": 0.75,
}


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
@elemental_retry
async def elemental_fire_position_size(
    symbol: str,
    portfolio_value: float,
    vedastro_score: float,
    dominant_planet: str,
    price_history: list[float],
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Calculate position size based on VedAstro score and volatility.

    V17 Constraints:
    - Max €2,000 per position
    - Max 2% of portfolio

    Args:
        symbol: Asset symbol
        portfolio_value: Total portfolio value in EUR
        vedastro_score: VedAstro strength score (0-100)
        dominant_planet: Dominant planet for the day
        price_history: Recent price history for volatility calc
        ctx: MCP context

    Returns:
        Position sizing recommendation
    """
    if ctx:
        ctx.info(f"Calculating Fire position size for {symbol}")

    # V17 logic: Calculate ATR-based volatility factor
    if len(price_history) < 20:
        vol_factor = 1.0
    else:
        # Simple volatility calculation
        returns = [
            (price_history[i] - price_history[i - 1]) / price_history[i - 1]
            for i in range(1, len(price_history))
        ]
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        volatility = variance**0.5

        vol_factor = max(0.5, min(2.0, 0.03 / (volatility + 0.001)))

    # VedAstro score → harmony factor (0.5-1.2)
    harmony_factor = 0.5 + (vedastro_score / 100) * 0.7

    # Streak factor
    streak = 0
    for i in range(1, min(6, len(price_history))):
        if price_history[-i] > price_history[-i - 1]:
            streak += 1
        else:
            break
    streak_factor = 1.0 + (streak * 0.05)

    # Planet multiplier
    planet_mult = PLANET_RISK_MULTIPLIERS.get(dominant_planet, 1.0)

    # Calculate position size
    base_pct = 0.015 * vol_factor * harmony_factor * streak_factor * planet_mult
    raw_size = portfolio_value * base_pct
    max_pct_size = portfolio_value * 0.02  # 2% max

    # V17: Apply €2k cap
    position_size = min(raw_size, max_pct_size, MAX_POSITION_EUR)

    if ctx:
        ctx.info(f"Position size: €{position_size:.2f} (raw: €{raw_size:.2f})")

    return {
        "position_size_eur": position_size,
        "max_position_eur": MAX_POSITION_EUR,
        "position_pct": position_size / portfolio_value if portfolio_value > 0 else 0,
        "sizing_factors": {
            "volatility": vol_factor,
            "harmony": harmony_factor,
            "streak": streak_factor,
            "planet": planet_mult,
        },
        "constraints_applied": ["max_2000_eur", "max_2pct_portfolio"],
    }


@circuit_breaker(failure_threshold=3, timeout_seconds=5)
async def elemental_earth_entry_check(
    symbol: str, trade_history: list[dict[str, Any]], ctx: Context = None
) -> dict[str, Any]:
    """
    Check if entry is allowed (3-loss rule).

    V17 Logic:
    - Block entry after 3 consecutive losses

    Args:
        symbol: Asset symbol
        trade_history: List of recent trades with 'pnl' and 'win' fields
        ctx: MCP context

    Returns:
        Entry permission and blocking reasons
    """
    if ctx:
        ctx.info(f"Checking Earth entry for {symbol}")

    # Get recent trades for this symbol
    recent = [t for t in trade_history if t.get("symbol") == symbol][-20:]

    # Check 3 consecutive losses
    consecutive_losses = 0
    for trade in reversed(recent):
        if not trade.get("win", True):
            consecutive_losses += 1
        else:
            break

    can_enter = consecutive_losses < 3

    if ctx:
        ctx.info(f"Entry allowed: {can_enter} (consecutive losses: {consecutive_losses})")

    return {
        "can_enter": can_enter,
        "blocking_reason": "3_consecutive_losses" if not can_enter else None,
        "recent_loss_count": sum(1 for t in recent if not t.get("win", True)),
        "consecutive_losses": consecutive_losses,
    }


@circuit_breaker(failure_threshold=3, timeout_seconds=5)
async def elemental_earth_exit_check(
    symbol: str,
    entry_date: str,
    current_date: str,
    entry_price: float,
    current_price: float,
    peak_price: float,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Check if position should be exited.

    V17 Constraints:
    - Max 60 days hold
    - Trailing stop: +40% peak → -15% drop = exit
    - Hard stop: -15% from entry

    Args:
        symbol: Asset symbol
        entry_date: Entry date (ISO format)
        current_date: Current date (ISO format)
        entry_price: Entry price
        current_price: Current price
        peak_price: Highest price since entry
        ctx: MCP context

    Returns:
        Exit recommendation
    """
    if ctx:
        ctx.info(f"Checking Earth exit for {symbol}")

    # Parse dates
    entry = datetime.fromisoformat(entry_date.replace("Z", "+00:00"))
    current = datetime.fromisoformat(current_date.replace("Z", "+00:00"))
    days_held = (current - entry).days

    # Calculate P&L
    pnl_pct = (current_price - entry_price) / entry_price
    peak_pnl_pct = (peak_price - entry_price) / entry_price
    drawdown_from_peak = (peak_price - current_price) / peak_price if peak_price > 0 else 0

    exit_signals = []

    # 60-day failsafe
    if days_held >= MAX_HOLD_DAYS:
        exit_signals.append(f"max_hold_days_{MAX_HOLD_DAYS}")

    # Trailing stop
    trailing_stop_active = peak_pnl_pct >= TRAILING_STOP_THRESHOLD
    if trailing_stop_active and drawdown_from_peak >= TRAILING_STOP_DISTANCE:
        exit_signals.append(f"trailing_stop_{drawdown_from_peak:.1%}")

    # Hard stop
    if drawdown_from_peak > 0.15 and pnl_pct < 0:
        exit_signals.append(f"hard_stop_{drawdown_from_peak:.1%}")

    should_exit = len(exit_signals) > 0

    if ctx:
        ctx.info(f"Exit recommended: {should_exit} (signals: {exit_signals})")

    return {
        "should_exit": should_exit,
        "exit_reasons": exit_signals,
        "days_held": days_held,
        "pnl_pct": pnl_pct,
        "peak_pnl_pct": peak_pnl_pct,
        "trailing_stop_active": trailing_stop_active,
    }


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
async def elemental_water_regime_check(
    symbol: str, prices: list[float], ctx: Context = None
) -> dict[str, Any]:
    """
    Check macro regime and hedge signals.

    Args:
        symbol: Asset symbol
        prices: Price history (min 20 points)
        ctx: MCP context

    Returns:
        Regime assessment and hedge recommendations
    """
    if ctx:
        ctx.info(f"Checking Water regime for {symbol}")

    if len(prices) < 20:
        return {
            "regime": "neutral",
            "risk_on_score": 0.5,
            "hedge_symbol": None,
            "hedge_confidence": 0.0,
            "reason": "insufficient_data",
        }

    # Calculate metrics
    price_change_30d = (prices[-1] - prices[-min(30, len(prices))]) / prices[-min(30, len(prices))]
    advancing = sum(1 for i in range(1, min(20, len(prices))) if prices[-i] > prices[-i - 1])
    total = min(19, len(prices) - 1)
    advance_ratio = advancing / total if total > 0 else 0.5

    # Determine regime
    if advance_ratio > 0.6 and price_change_30d > 0.10:
        regime = "expansion"
        risk_on = 0.8
    elif advance_ratio < 0.4 and price_change_30d < -0.10:
        regime = "contraction"
        risk_on = 0.2
    elif price_change_30d > 0:
        regime = "recovery"
        risk_on = 0.6
    else:
        regime = "neutral"
        risk_on = 0.5

    # Hedge signal (V17: hedge when risk_on < 0.35)
    hedge_pairs = {"SPY": "SH", "QQQ": "PSQ", "IWM": "RWM", "TLT": "TBF"}
    hedge_sym = hedge_pairs.get(symbol)
    hedge_conf = 0.0

    if hedge_sym and risk_on < 0.35:
        hedge_conf = 0.70 + (0.35 - risk_on) * 0.5
        hedge_conf = min(hedge_conf, 0.85)

    if ctx:
        ctx.info(f"Regime: {regime} (risk_on: {risk_on:.2f})")

    return {
        "regime": regime,
        "risk_on_score": risk_on,
        "hedge_symbol": hedge_sym if hedge_conf > 0 else None,
        "hedge_confidence": hedge_conf,
        "advance_ratio": advance_ratio,
        "price_change_30d": price_change_30d,
    }


@circuit_breaker(failure_threshold=3, timeout_seconds=5)
async def elemental_ether_consensus(
    fire_vote: float,
    earth_vote: float,
    water_vote: float,
    air_vote: float,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Synthesize elemental consensus.

    Args:
        fire_vote: Fire element score (0-1)
        earth_vote: Earth element score (0-1)
        water_vote: Water element score (0-1)
        air_vote: Air element score (0-1)
        ctx: MCP context

    Returns:
        Consensus decision
    """
    if ctx:
        ctx.info("Calculating Ether consensus")

    # Calculate harmony (weighted average)
    weights = {"fire": 0.25, "earth": 0.30, "water": 0.25, "air": 0.20}
    harmony = (
        fire_vote * weights["fire"]
        + earth_vote * weights["earth"]
        + water_vote * weights["water"]
        + air_vote * weights["air"]
    )

    # V17 threshold: harmony > 0.45 = approved
    approved = harmony > 0.45

    # Determine dominant element
    votes = {
        "fire": fire_vote,
        "earth": earth_vote,
        "water": water_vote,
        "air": air_vote,
    }
    dominant = max(votes, key=votes.get)

    if ctx:
        ctx.info(f"Consensus: {harmony:.2f} (approved: {approved}, dominant: {dominant})")

    return {
        "harmony_score": harmony,
        "approved": approved,
        "threshold": 0.45,
        "elemental_breakdown": votes,
        "dominant_element": dominant,
    }
