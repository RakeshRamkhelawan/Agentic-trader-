"""
Elemental Agent Manager V11 - TRADING FREQUENCY FIX + PARTIAL EXITS

V11 Key Changes:
- Fix: Trading frequency (daily iteration confirmed)
- Partial exit bij grote winst (Earth: 50% verkopen als winst > 2.5x avg)
- Crypto memory decay: 0.85 (vs 0.95 equity) voor sneller vergeten slechte trades
- Normal exits via profit targets

Fire Agent sizing ONGEWIJZIGD van v10
"""

import logging
import os
import statistics
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ElementalAgentsV11")


# ============ V11: NAVAGRAHA RISK MULTIPLIERS ============
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

# V11: Thresholds ongewijzigd van v10
PLANET_THRESHOLDS = {
    "SUN": 0.55,
    "MOON": 0.53,
    "MARS": 0.60,
    "MERCURY": 0.57,
    "JUPITER": 0.60,
    "VENUS": 0.57,
    "SATURN": 0.50,
    "RAHU": 0.65,
    "KETU": 0.58,
}

ASSET_CLASSES = {
    "crypto": [
        "BTC",
        "ETH",
        "SOL",
        "AVAX",
        "LINK",
        "DOT",
        "ADA",
        "XRP",
        "DOGE",
        "LTC",
        "ATOM",
        "ALGO",
        "VET",
        "TRX",
        "XLM",
        "UNI",
        "MATIC",
        "AAVE",
        "FIL",
        "ETC",
    ],
    "equity_us": [
        "AAPL",
        "MSFT",
        "GOOGL",
        "META",
        "NVDA",
        "AMZN",
        "TSLA",
        "AMD",
        "CRM",
        "ADBE",
        "NFLX",
        "ORCL",
        "INTC",
        "PYPL",
        "ROKU",
        "ZM",
        "COIN",
        "SNOW",
        "UBER",
        "IBM",
    ],
    "equity_eu": ["ASML", "SAP", "AIR", "ROG", "NESN", "TTE", "SHEL"],
    "etf": ["SPY", "QQQ", "VTI", "IWM", "EEM", "EFA", "GLD", "TLT", "USO", "VIX"],
}

# V11: Crypto memory decay zwaarder
ASSET_DECAY = {
    "crypto": 0.85,
    "equity_us": 0.95,
    "equity_eu": 0.95,
    "etf": 0.98,
}

WARM_START_CONFIDENCE = {
    "crypto": 0.72,
    "equity_us": 0.85,
    "equity_eu": 0.78,
    "etf": 0.88,
}

IPO_DATES = {
    "COIN": "2021-04-14",
    "SNOW": "2020-09-16",
    "UBER": "2019-05-10",
    "ZM": "2019-04-18",
    "ROKU": "2017-09-28",
}


@dataclass
class MacroSignal:
    risk_on_score: float
    regime: str


# ============ V11: EARTH AGENT - PARTIAL EXITS + CRYPTO DECAY ============


class EarthAgentV11:
    """Earth Agent with partial exits and crypto memory decay"""

    def __init__(self):
        # V11: Memory met decay weights
        self.symbol_memory: Dict[str, List[Dict]] = defaultdict(list)
        self.win_rates: Dict[str, float] = {}

        # Entry tracking
        self.entry_confidences: Dict[str, float] = {}
        self.entry_dates: Dict[str, datetime] = {}

        # V11: Track partial exit status
        self.partial_exit_done: Dict[str, bool] = {}

    def record_entry(self, symbol: str, entry_date: datetime):
        """V11: Record entry for position review"""
        self.entry_confidences[symbol] = self.calculate_confidence(symbol)
        self.entry_dates[symbol] = entry_date
        self.partial_exit_done[symbol] = False

    def record_exit(self, symbol: str, pnl: float, win: bool):
        """V11: Record exit with crypto memory decay"""
        asset_class = self._get_asset_class(symbol)
        decay = ASSET_DECAY.get(asset_class, 0.95)

        # V11: Add trade with decay weight
        self.symbol_memory[symbol].append(
            {"pnl": pnl, "win": win, "timestamp": datetime.utcnow(), "decay": decay}
        )

        # V11: Apply decay to old trades
        self._apply_decay(symbol)

        # Clear entry memory
        self.entry_confidences.pop(symbol, None)
        self.entry_dates.pop(symbol, None)
        self.partial_exit_done.pop(symbol, None)

    def _apply_decay(self, symbol: str):
        """V11: Apply exponential decay to historical trades"""
        if len(self.symbol_memory[symbol]) > 20:
            # Keep only recent trades with decay applied
            trades = self.symbol_memory[symbol]
            for i, trade in enumerate(trades[:-1]):  # Skip newest
                trade["decay"] *= ASSET_DECAY.get(self._get_asset_class(symbol), 0.95)

    def evaluate_open_position(self, symbol: str, current_date: datetime) -> str:
        """V11: Earth exit evaluation (minimum 5 dagen holding)"""
        if symbol not in self.entry_confidences or symbol not in self.entry_dates:
            return "HOLD"

        entry_date = self.entry_dates[symbol]
        days_held = (current_date - entry_date).days
        if days_held < 5:
            return "HOLD"

        entry_conf = self.entry_confidences[symbol]
        current_conf = self.calculate_confidence(symbol)

        if current_conf < entry_conf * 0.60:
            return "EXIT"
        return "HOLD"

    def evaluate_profit_target(self, symbol: str, unrealized_pnl: float) -> str:
        """
        V11: Realiseer 50% van de positie als winst > 2.5x gemiddelde
        """
        if self.partial_exit_done.get(symbol, False):
            return "HOLD"

        hist_avg = self.get_avg_winner(symbol)
        if hist_avg > 0 and unrealized_pnl > hist_avg * 2.5:
            self.partial_exit_done[symbol] = True
            return "PARTIAL_EXIT"
        return "HOLD"

    def get_avg_winner(self, symbol: str) -> float:
        """V11: Get decay-weighted average winner"""
        history = self.symbol_memory[symbol]
        if not history:
            return 100.0  # Default

        winners = [t for t in history if t["win"]]
        if not winners:
            return 100.0

        # Weighted average with decay
        weighted_sum = sum(t["pnl"] * t.get("decay", 1.0) for t in winners)
        weight_sum = sum(t.get("decay", 1.0) for t in winners)

        return weighted_sum / weight_sum if weight_sum > 0 else 100.0

    def _get_asset_class(self, symbol: str) -> str:
        for cls, symbols in ASSET_CLASSES.items():
            if symbol in symbols:
                return cls
        return "equity_us"

    def calculate_confidence(self, symbol: str) -> float:
        """V11: Confidence with weighted historical performance"""
        history = self.symbol_memory[symbol]
        asset_class = self._get_asset_class(symbol)

        if len(history) < 5:
            return WARM_START_CONFIDENCE.get(asset_class, 0.80)

        # V11: Weighted win rate with decay
        weighted_wins = sum(t.get("decay", 1.0) for t in history if t["win"])
        weighted_total = sum(t.get("decay", 1.0) for t in history)

        recent_win_rate = weighted_wins / weighted_total if weighted_total > 0 else 0.5

        # Weighted avg pnl
        weighted_pnl = sum(t["pnl"] * t.get("decay", 1.0) for t in history)
        avg_pnl = weighted_pnl / weighted_total if weighted_total > 0 else 0

        base = 0.4 + (recent_win_rate * 0.5)
        pnl_factor = min(max(avg_pnl / 100, -0.15), 0.15)

        confidence = base + pnl_factor
        warm_start = WARM_START_CONFIDENCE.get(asset_class, 0.80)
        blended = (confidence * 0.7) + (warm_start * 0.3)

        return min(max(blended, 0.40), 0.95)


# ============ V11: FIRE AGENT ============


class FireAgentV11:
    """Fire Agent - unchanged from v10"""

    def __init__(self):
        self.loss_streaks: Dict[str, int] = defaultdict(int)
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
        self.PLANET_MULTIPLIERS = PLANET_RISK_MULTIPLIERS

        self.entry_atr: Dict[str, float] = {}
        self.position_peaks: Dict[str, float] = {}

    def record_price(self, symbol: str, price: float):
        self.price_history[symbol].append(price)

    def record_entry(self, symbol: str, entry_price: float):
        self.entry_atr[symbol] = self.calculate_atr_pct(symbol)
        self.position_peaks[symbol] = entry_price

    def update_peak(self, symbol: str, current_price: float):
        if symbol in self.position_peaks:
            self.position_peaks[symbol] = max(
                self.position_peaks[symbol], current_price
            )

    def record_exit(self, symbol: str, pnl: float):
        self.record_outcome(symbol, pnl)
        self.entry_atr.pop(symbol, None)
        self.position_peaks.pop(symbol, None)

    def record_outcome(self, symbol: str, pnl: float):
        if pnl < 0:
            self.loss_streaks[symbol] += 1
        else:
            self.loss_streaks[symbol] = 0

    def calculate_atr_pct(self, symbol: str) -> float:
        prices = list(self.price_history[symbol])
        if len(prices) < 5:
            return 0.03
        changes = [abs(prices[i] / prices[i - 1] - 1) for i in range(1, len(prices))]
        return statistics.mean(changes)

    def calculate_confidence(self, symbol: str) -> float:
        streak = self.loss_streaks[symbol]
        atr_pct = self.calculate_atr_pct(symbol)

        streak_penalty = min(streak * 0.08, 0.45)
        vol_penalty = min(atr_pct / 0.05, 0.30)

        confidence = 0.92 - streak_penalty - vol_penalty
        return max(confidence, 0.37)

    def evaluate_open_position(self, symbol: str, current_price: float) -> str:
        """V11: Fire exit evaluation (min 10 dagen window)"""
        if symbol not in self.entry_atr:
            return "HOLD"

        if len(self.price_history[symbol]) < 10:
            return "HOLD"

        entry_atr = self.entry_atr[symbol]
        current_atr = self.calculate_atr_pct(symbol)
        peak_price = self.position_peaks.get(symbol, current_price)

        vol_ratio = current_atr / max(entry_atr, 0.001)
        peak_drawdown = (current_price / peak_price) - 1

        if vol_ratio > 4.0 and peak_drawdown < -0.15:
            return "EXIT"
        if vol_ratio > 6.0:
            return "EXIT"
        return "HOLD"

    def calculate_position_size(
        self, symbol: str, portfolio_value: float, harmony: float, dominant_planet: str
    ) -> float:
        atr_pct = self.calculate_atr_pct(symbol)
        streak = self.loss_streaks[symbol]

        vol_factor = 1.0 / (1.0 + atr_pct * 6)
        harmony_factor = harmony**2
        streak_factor = 0.5**streak
        planet_mult = self.PLANET_MULTIPLIERS.get(dominant_planet, 1.0)

        base_pct = 0.015
        position_pct = (
            base_pct * vol_factor * harmony_factor * streak_factor * planet_mult
        )

        return portfolio_value * position_pct


# ============ V11: WATER AGENT ============


class WaterAgentV11:
    """Water Agent - unchanged from v10"""

    def __init__(self):
        self.ASSET_CLASSES = ASSET_CLASSES
        self.entry_macro_score: Dict[str, float] = {}

    def record_entry(self, symbol: str, macro_signal: MacroSignal):
        self.entry_macro_score[symbol] = macro_signal.risk_on_score

    def record_exit(self, symbol: str):
        self.entry_macro_score.pop(symbol, None)

    def _get_asset_class(self, symbol: str) -> str:
        for cls, syms in self.ASSET_CLASSES.items():
            if symbol in syms:
                return cls
        return "equity_us"

    def get_macro_signal(self, prices: List[float]) -> MacroSignal:
        if len(prices) < 20:
            return MacroSignal(risk_on_score=0.5, regime="neutral")

        price_change_30d = (prices[-1] - prices[-min(30, len(prices))]) / prices[
            -min(30, len(prices))
        ]

        advancing = sum(
            1 for i in range(1, min(20, len(prices))) if prices[-i] > prices[-i - 1]
        )
        total = min(19, len(prices) - 1)

        if total > 0:
            advance_ratio = advancing / total
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
        else:
            regime = "neutral"
            risk_on = 0.5

        return MacroSignal(risk_on_score=risk_on, regime=regime)

    def calculate_confidence(self, symbol: str, macro_signal: MacroSignal) -> float:
        asset_class = self._get_asset_class(symbol)
        base_conf = WARM_START_CONFIDENCE.get(asset_class, 0.80)

        if macro_signal.regime == "expansion":
            confidence = base_conf * 1.05
        elif macro_signal.regime == "contraction":
            confidence = base_conf * 0.85
        else:
            confidence = base_conf

        return min(confidence, 0.90)

    def evaluate_open_position(self, symbol: str, macro_signal: MacroSignal) -> str:
        if symbol not in self.entry_macro_score:
            return "HOLD"

        entry_risk_on = self.entry_macro_score[symbol]
        current_risk_on = macro_signal.risk_on_score
        asset_class = self._get_asset_class(symbol)

        shift_threshold = 0.35 if asset_class == "crypto" else 0.50

        if (entry_risk_on - current_risk_on) > shift_threshold:
            return "EXIT"
        return "HOLD"


# ============ V11: AIR AGENT ============


class AirAgentV11:
    """Air Agent - unchanged"""

    def __init__(self):
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))

    def update_price(self, symbol: str, price: float):
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=50)
        self.price_history[symbol].append(price)

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        if len(gains) < period:
            return 50.0
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def calculate_confidence(self, symbol: str) -> float:
        prices = list(self.price_history.get(symbol, []))

        if len(prices) < 20:
            return 0.60

        rsi = self._calculate_rsi(prices)
        ema20 = sum(prices[-20:]) / 20
        ema50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else ema20

        trend_up = ema20 > ema50

        if trend_up and rsi < 70:
            return 0.75
        elif not trend_up and rsi > 30:
            return 0.55
        elif rsi < 35:
            return 0.60
        elif rsi > 65:
            return 0.45
        return 0.55


# ============ V11: ETHER ORCHESTRATOR ============


class EtherOrchestratorV11:
    """Ether - unchanged from v10"""

    AGENT_WEIGHTS = {
        "fire": 0.30,
        "earth": 0.25,
        "water": 0.20,
        "air": 0.15,
        "ether": 0.10,
    }

    def synthesize(
        self, fire_conf: float, water_conf: float, air_conf: float, earth_conf: float
    ) -> Tuple[float, bool]:
        weighted_harmony = (
            fire_conf * self.AGENT_WEIGHTS["fire"]
            + water_conf * self.AGENT_WEIGHTS["water"]
            + air_conf * self.AGENT_WEIGHTS["air"]
            + earth_conf * self.AGENT_WEIGHTS["earth"]
        )

        values = [fire_conf, water_conf, air_conf, earth_conf]
        spread = max(values) - min(values)
        disagreement_penalty = spread * 0.05

        harmony = weighted_harmony - disagreement_penalty
        harmony = min(max(harmony, 0.0), 1.0)

        min_threshold = 0.35
        agents_above = sum(1 for c in values if c >= min_threshold)
        consensus = agents_above >= 4

        return harmony, consensus

    def should_execute(
        self, harmony: float, consensus: bool, dominant_planet: str
    ) -> bool:
        threshold = PLANET_THRESHOLDS.get(dominant_planet, 0.55)
        return consensus and harmony >= threshold


# ============ V11: MAIN MANAGER ============


class ElementalAgentManagerV11:
    """V11: Partial exits + Crypto memory decay + Daily frequency"""

    SLIPPAGE_PCT = 0.001
    COMMISSION_PCT = 0.0005

    def __init__(self):
        self.fire_agent = FireAgentV11()
        self.water_agent = WaterAgentV11()
        self.air_agent = AirAgentV11()
        self.earth_agent = EarthAgentV11()
        self.ether_orchestrator = EtherOrchestratorV11()

        self.agent_confidence_history: Dict[str, List[float]] = {
            "fire": [],
            "water": [],
            "air": [],
            "earth": [],
            "ether": [],
        }
        self.consensus_count = 0
        self.total_cycles = 0
        self.execute_count = 0
        self.position_review_exits = 0
        self.partial_exits = 0
        self.normal_exits = 0

    def is_symbol_available(self, symbol: str, cycle_date: datetime) -> bool:
        if symbol in IPO_DATES:
            ipo_date = datetime.strptime(IPO_DATES[symbol], "%Y-%m-%d")
            return cycle_date >= ipo_date
        return True

    def record_trade_outcome(self, symbol: str, pnl: float, win: bool):
        self.earth_agent.record_exit(symbol, pnl, win)
        self.fire_agent.record_exit(symbol, pnl)
        self.water_agent.record_exit(symbol)

    def evaluate_open_position(
        self,
        symbol: str,
        current_price: float,
        macro_signal: MacroSignal,
        current_date: datetime,
        entry_price: float,
        quantity: float,
    ) -> Tuple[str, str]:
        """
        V11: Position Review Loop with partial exit support
        Returns: (action, reason) where action is 'HOLD', 'EXIT', or 'PARTIAL_EXIT'
        """
        self.fire_agent.update_peak(symbol, current_price)

        # Calculate unrealized PnL
        unrealized_pnl = (current_price - entry_price) * quantity

        # V11: Check for partial profit target
        partial_action = self.earth_agent.evaluate_profit_target(symbol, unrealized_pnl)
        if partial_action == "PARTIAL_EXIT":
            self.partial_exits += 1
            return "PARTIAL_EXIT", "earth_profit_target"

        # Regular position review
        earth_exit = self.earth_agent.evaluate_open_position(symbol, current_date)
        fire_exit = self.fire_agent.evaluate_open_position(symbol, current_price)
        water_exit = self.water_agent.evaluate_open_position(symbol, macro_signal)

        if earth_exit == "EXIT":
            return "EXIT", "earth_confidence_drop"
        if fire_exit == "EXIT":
            return "EXIT", "fire_vol_explosion"
        if water_exit == "EXIT":
            return "EXIT", "water_regime_shift"

        return "HOLD", "hold"

    def process_entry_cycle(
        self,
        symbol: str,
        current_price: float,
        portfolio_value: float,
        cycle_date: datetime,
        prana_level: float = 85.0,
    ) -> Optional[Dict]:
        """V11: Process entry evaluation"""
        self.fire_agent.record_price(symbol, current_price)
        self.air_agent.update_price(symbol, current_price)

        self.total_cycles += 1

        planets = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]
        dominant_planet = planets[cycle_date.day % 7]

        rahu_active = (cycle_date.day % 8) == 0
        if rahu_active:
            return None

        if prana_level < 10:
            return None

        prices = list(self.fire_agent.price_history.get(symbol, []))
        macro_signal = self.water_agent.get_macro_signal(prices)

        fire_conf = self.fire_agent.calculate_confidence(symbol)
        water_conf = self.water_agent.calculate_confidence(symbol, macro_signal)
        air_conf = self.air_agent.calculate_confidence(symbol)
        earth_conf = self.earth_agent.calculate_confidence(symbol)

        harmony, consensus = self.ether_orchestrator.synthesize(
            fire_conf, water_conf, air_conf, earth_conf
        )

        if consensus:
            self.consensus_count += 1

        self.agent_confidence_history["fire"].append(fire_conf)
        self.agent_confidence_history["water"].append(water_conf)
        self.agent_confidence_history["air"].append(air_conf)
        self.agent_confidence_history["earth"].append(earth_conf)
        self.agent_confidence_history["ether"].append(harmony)

        if not self.ether_orchestrator.should_execute(
            harmony, consensus, dominant_planet
        ):
            return None

        position_size = self.fire_agent.calculate_position_size(
            symbol, portfolio_value, harmony, dominant_planet
        )

        entry_price = current_price * (1 + self.SLIPPAGE_PCT)
        commission = position_size * self.COMMISSION_PCT
        actual_size = position_size - commission
        quantity = actual_size / entry_price

        if quantity <= 0:
            return None

        self.execute_count += 1

        self.earth_agent.record_entry(symbol, cycle_date)
        self.fire_agent.record_entry(symbol, entry_price)
        self.water_agent.record_entry(symbol, macro_signal)

        return {
            "symbol": symbol,
            "action": "BUY",
            "entry_price": entry_price,
            "quantity": quantity,
            "position_size": position_size,
            "harmony": harmony,
            "planet": dominant_planet,
            "fire_conf": fire_conf,
            "water_conf": water_conf,
            "air_conf": air_conf,
            "earth_conf": earth_conf,
        }

    def get_agent_stats(self) -> Dict[str, Any]:
        stats = {}
        for agent, confidences in self.agent_confidence_history.items():
            if confidences:
                stats[agent] = {
                    "avg_confidence": sum(confidences) / len(confidences),
                    "min_confidence": min(confidences),
                    "max_confidence": max(confidences),
                    "samples": len(confidences),
                }

        stats["consensus_achieved_pct"] = (
            (self.consensus_count / self.total_cycles * 100)
            if self.total_cycles > 0
            else 0
        )
        stats["execute_rate_pct"] = (
            (self.execute_count / self.total_cycles * 100)
            if self.total_cycles > 0
            else 0
        )
        stats["total_cycles"] = self.total_cycles
        stats["consensus_count"] = self.consensus_count
        stats["execute_count"] = self.execute_count
        stats["position_review_exits"] = self.position_review_exits
        stats["partial_exits"] = self.partial_exits
        stats["normal_exits"] = self.normal_exits

        return stats
