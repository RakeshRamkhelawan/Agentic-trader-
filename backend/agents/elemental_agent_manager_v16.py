"""
Elemental Agent Manager V16 - THRESHOLD CALIBRATION

V16 Key Changes (Pure Calibration):
1. Fire floor: 0.35 (was 0.50) - V10 restoration
2. Earth floor: 0.45 (was 0.55) - V10 restoration  
3. Ether harmony: 0.45 (was 0.50) - Looser consensus
4. Planet thresholds: Lowered marginally
5. AAVE removed from universe (data anomaly)

Retained from V15:
- Trailing stop (+40% → -15%)
- Position cap €2,000
- 60-day failsafe
- Daily cycle counting
- Water TLT inverse logic
- Earth 3-loss entry blocking

STRICT PRESERVATION (DO NOT MODIFY):
- Daily cycle loop structure
- Water TLT inverse logic
- Earth should_enter 3-loss threshold
- Position sizing caps
- Trailing stop logic
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
logger = logging.getLogger("ElementalAgentsV16")


# ============ V16: NAVAGRAHA RISK MULTIPLIERS ============
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

# V16: LOWERED planet thresholds (marginal relaxation)
PLANET_THRESHOLDS = {
    "SUN": 0.52,  # was 0.55 → -0.03
    "MOON": 0.50,  # was 0.53 → -0.03
    "MARS": 0.57,  # was 0.60 → -0.03
    "MERCURY": 0.51,  # was 0.54 → -0.03
    "JUPITER": 0.54,  # was 0.57 → -0.03
    "VENUS": 0.51,  # was 0.54 → -0.03
    "SATURN": 0.47,  # was 0.50 → -0.03
    "RAHU": 0.59,  # was 0.62 → -0.03
    "KETU": 0.55,  # was 0.58 → -0.03
}

# V16: Ether harmony threshold lowered
ETHER_MIN_HARMONY = 0.45  # was 0.50

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
        "FIL",
        "ETC",
    ],  # AAVE removed (data anomaly)
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
    "bond": ["TLT", "IEF", "AGG", "BND", "GOVT"],
    "inverse_etf": ["SH", "PSQ", "RWM", "TBF"],
}

# V12: Hedge pairs (primary -> inverse)
HEDGE_PAIRS = {
    "SPY": "SH",
    "QQQ": "PSQ",
    "IWM": "RWM",
    "TLT": "TBF",
}

# V12: Inverse ETF set for quick lookup
INVERSE_ETFS = {"SH", "PSQ", "RWM", "TBF"}

# V12: Bond symbols for inverse logic
BOND_SYMBOLS = {"TLT", "IEF", "AGG", "BND", "TBF", "GOVT"}

WARM_START_CONFIDENCE = {
    "crypto": 0.72,
    "equity_us": 0.85,
    "equity_eu": 0.78,
    "etf": 0.88,
}

# IPO dates for survivorship bias mitigation
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


# ============ V16: EARTH AGENT - RESTORED FLOOR ============


class EarthAgentV16:
    """
    Earth Agent with:
    - 3 consecutive losses entry blocking
    - 60-day time-based exit
    - Trailing stop coordination
    - V16: Floor restored to 0.45 (was 0.55)
    """

    MAX_HOLD_DAYS = 60

    def __init__(self):
        self.symbol_memory: Dict[str, deque] = defaultdict(lambda: deque(maxlen=20))
        self.win_rates: Dict[str, float] = {}
        self.entry_dates: Dict[str, datetime] = {}
        self.peak_unrealized_pnl: Dict[str, float] = {}
        self.trailing_stop_active: Dict[str, bool] = {}

    def record_entry(self, symbol: str, entry_date: datetime):
        self.entry_dates[symbol] = entry_date
        self.peak_unrealized_pnl[symbol] = 0.0
        self.trailing_stop_active[symbol] = False

    def record_exit(self, symbol: str, pnl: float, win: bool):
        self.symbol_memory[symbol].append(
            {"pnl": pnl, "win": win, "timestamp": datetime.now()}
        )

        history = list(self.symbol_memory[symbol])
        if history:
            wins = sum(1 for h in history if h["win"])
            self.win_rates[symbol] = wins / len(history)

        self.entry_dates.pop(symbol, None)
        self.peak_unrealized_pnl.pop(symbol, None)
        self.trailing_stop_active.pop(symbol, None)

    def should_enter(self, symbol: str) -> bool:
        """V16: 3 consecutive losses entry blocking (preserved)"""
        recent = list(self.symbol_memory.get(symbol, []))
        if len(recent) >= 3:
            last_three = recent[-3:]
            if all(not t["win"] for t in last_three):
                return False
        return True

    def update_unrealized_pnl(self, symbol: str, unrealized_pnl_pct: float):
        if symbol not in self.peak_unrealized_pnl:
            self.peak_unrealized_pnl[symbol] = 0.0
            self.trailing_stop_active[symbol] = False

        if unrealized_pnl_pct > self.peak_unrealized_pnl[symbol]:
            self.peak_unrealized_pnl[symbol] = unrealized_pnl_pct

        if self.peak_unrealized_pnl[symbol] >= 0.40:
            self.trailing_stop_active[symbol] = True

    def check_trailing_stop(self, symbol: str, current_pnl_pct: float) -> bool:
        if not self.trailing_stop_active.get(symbol, False):
            return False

        peak = self.peak_unrealized_pnl.get(symbol, 0.0)
        if peak - current_pnl_pct >= 0.15:
            return True

        return False

    def evaluate_open_position(
        self, symbol: str, current_price: float, current_date: datetime
    ) -> Tuple[bool, str]:
        """V16: Position evaluation with time-based and trailing stop"""
        entry_date = self.entry_dates.get(symbol)
        if not entry_date:
            return False, ""

        days_held = (current_date - entry_date).days
        if days_held >= self.MAX_HOLD_DAYS:
            return True, "time_based"

        return False, ""

    def calculate_confidence(self, symbol: str) -> float:
        """
        V16: Earth confidence with RESTORED floor 0.45 (was 0.55)
        Masterprompt: return max(0.45, min(0.95, final_score))
        """
        history = list(self.symbol_memory.get(symbol, []))
        if not history:
            base_conf = 0.85
        else:
            wins = sum(1 for h in history if h["win"])
            win_rate = wins / len(history)

            recent = history[-5:]
            recent_wins = sum(1 for h in recent if h["win"])
            recent_rate = recent_wins / len(recent) if recent else 0.5

            base_conf = 0.6 * win_rate + 0.4 * recent_rate

        # V16: Floor restored to 0.45 (was 0.55)
        return max(0.45, min(0.95, base_conf))


# ============ V16: FIRE AGENT - RESTORED FLOOR ============


class FireAgentV16:
    """
    Fire Agent with:
    - ATR-based position sizing
    - Hard €2,000 cap (preserved from V15)
    - V16: Floor restored to 0.35 (was 0.50)
    """

    MAX_POSITION_EUR = 2000.0

    def __init__(self):
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
        self.entry_prices: Dict[str, float] = {}
        self.peak_prices: Dict[str, float] = {}
        self.max_position_pct = 0.10

    def record_price(self, symbol: str, price: float):
        self.price_history[symbol].append(price)

    def record_entry(self, symbol: str, entry_price: float):
        self.entry_prices[symbol] = entry_price
        self.peak_prices[symbol] = entry_price

    def record_exit(self, symbol: str, pnl: float):
        self.entry_prices.pop(symbol, None)
        self.peak_prices.pop(symbol, None)

    def _calculate_atr(self, symbol: str, period: int = 14) -> float:
        prices = list(self.price_history.get(symbol, []))
        if len(prices) < period + 1:
            return 0.02

        tr_list = []
        for i in range(1, min(period + 1, len(prices))):
            high = prices[-i]
            low = prices[-i - 1]
            tr = abs(high - low) / low if low > 0 else 0
            tr_list.append(tr)

        return statistics.mean(tr_list) if tr_list else 0.02

    def calculate_position_size(
        self, symbol: str, portfolio_value: float, harmony: float, dominant_planet: str
    ) -> float:
        """
        V16: ATR sizing with €2,000 cap (preserved from V15)
        """
        prices = list(self.price_history.get(symbol, []))
        if len(prices) < 20:
            raw_size = portfolio_value * 0.01
        else:
            atr = self._calculate_atr(symbol)
            vol_factor = max(0.5, min(2.0, 0.03 / (atr + 0.001)))
            harmony_factor = 0.8 + (harmony * 0.4)

            streak = 0
            history = list(self.price_history.get(symbol, []))
            for i in range(1, min(6, len(history))):
                if history[-i] > history[-i - 1]:
                    streak += 1
                else:
                    break
            streak_factor = 1.0 + (streak * 0.05)

            planet_mult = PLANET_RISK_MULTIPLIERS.get(dominant_planet, 1.0)

            base_pct = 0.015
            position_pct = (
                base_pct * vol_factor * harmony_factor * streak_factor * planet_mult
            )
            raw_size = portfolio_value * position_pct

        max_pct_size = portfolio_value * 0.02
        capped_size = min(raw_size, max_pct_size, self.MAX_POSITION_EUR)

        return capped_size

    def calculate_confidence(self, symbol: str) -> float:
        """
        V16: Fire confidence with RESTORED floor 0.35 (was 0.50)
        Masterprompt: return max(0.35, min(0.95, final_score))
        """
        prices = list(self.price_history.get(symbol, []))
        if len(prices) < 20:
            base_conf = 0.70
        else:
            returns = [
                (prices[i] - prices[i - 1]) / prices[i - 1]
                for i in range(1, len(prices))
            ]
            vol = statistics.stdev(returns) if len(returns) > 1 else 0.02

            if vol < 0.015:
                vol_conf = 0.75
            elif vol < 0.025:
                vol_conf = 0.60
            else:
                vol_conf = 0.45

            if len(prices) >= 10:
                trend = (prices[-1] - prices[-10]) / prices[-10]
                if trend > 0.05:
                    trend_conf = 0.70
                elif trend > 0:
                    trend_conf = 0.60
                else:
                    trend_conf = 0.50
            else:
                trend_conf = 0.55

            base_conf = 0.5 * vol_conf + 0.5 * trend_conf

        # V16: Floor restored to 0.35 (was 0.50)
        return max(0.35, min(0.95, base_conf))


# ============ V12: WATER AGENT (PRESERVED - DO NOT MODIFY) ============


class WaterAgentV12:
    """Water Agent - STRICTLY PRESERVED from V12/V15"""

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

    def get_hedge_signal(
        self, primary_symbol: str, macro_signal: MacroSignal
    ) -> Tuple[Optional[str], float]:
        hedge_sym = HEDGE_PAIRS.get(primary_symbol)
        if not hedge_sym:
            return None, 0.0

        risk_on = macro_signal.risk_on_score

        if risk_on < 0.35:
            hedge_conf = 0.70 + (0.35 - risk_on) * 0.5
            return hedge_sym, min(hedge_conf, 0.85)

        return None, 0.0

    def calculate_confidence(self, symbol: str, macro_signal: MacroSignal) -> float:
        if symbol in INVERSE_ETFS:
            risk_on = macro_signal.risk_on_score
            base = WARM_START_CONFIDENCE.get("etf", 0.88)
            return min(0.90, base * (1.5 - risk_on))

        asset_class = self._get_asset_class(symbol)
        base_conf = WARM_START_CONFIDENCE.get(asset_class, 0.80)

        if macro_signal.regime == "expansion":
            confidence = base_conf * 1.05
        elif macro_signal.regime == "contraction":
            confidence = base_conf * 0.85
        else:
            confidence = base_conf

        return min(0.95, max(0.60, confidence))


# ============ V12: AIR AGENT (PRESERVED) ============


class AirAgentV12:
    """Air Agent - PRESERVED"""

    def __init__(self):
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=30))
        self.sentiment_cache: Dict[str, Dict] = {}

    def update_price(self, symbol: str, price: float):
        self.price_history[symbol].append(price)

    def calculate_confidence(self, symbol: str, current_date: datetime = None) -> float:
        prices = list(self.price_history.get(symbol, []))
        if len(prices) < 10:
            return 0.60

        gains = []
        losses = []
        for i in range(1, min(15, len(prices))):
            change = prices[-i] - prices[-i - 1]
            if change > 0:
                gains.append(change)
            else:
                losses.append(abs(change))

        avg_gain = statistics.mean(gains) if gains else 0
        avg_loss = statistics.mean(losses) if losses else 0.001

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        if rsi > 70:
            momentum_conf = 0.75
        elif rsi > 50:
            momentum_conf = 0.65
        elif rsi > 30:
            momentum_conf = 0.55
        else:
            momentum_conf = 0.45

        return momentum_conf


# ============ V16: ETHER ORCHESTRATOR - LOWERED THRESHOLD ============


class EtherOrchestratorV16:
    """
    Ether - V16: Looser consensus for higher execution rate
    """

    AGENT_WEIGHTS = {
        "fire": 0.30,
        "earth": 0.25,
        "water": 0.20,
        "air": 0.15,
        "ether": 0.10,
    }

    # V16: Lowered harmony floor
    MIN_HARMONY = 0.45  # was 0.50

    def synthesize(
        self, fire_conf: float, water_conf: float, air_conf: float, earth_conf: float
    ) -> Tuple[float, bool]:
        """Synthesize agent confidences into harmony score"""

        weighted_harmony = (
            fire_conf * self.AGENT_WEIGHTS["fire"]
            + water_conf * self.AGENT_WEIGHTS["water"]
            + air_conf * self.AGENT_WEIGHTS["air"]
            + earth_conf * self.AGENT_WEIGHTS["earth"]
        )

        # V16: Lowered consensus threshold
        min_threshold = 0.45  # was 0.50
        consensus = all(
            [
                fire_conf >= min_threshold,
                water_conf >= min_threshold,
                air_conf >= min_threshold,
                earth_conf >= min_threshold,
            ]
        )

        return weighted_harmony, consensus

    def should_execute(
        self, harmony: float, consensus: bool, dominant_planet: str
    ) -> bool:
        """Determine if trade should execute"""
        threshold = PLANET_THRESHOLDS.get(dominant_planet, 0.55)
        # V16: Use lowered MIN_HARMONY
        return consensus and harmony >= max(threshold, self.MIN_HARMONY)


# ============ V16: ELEMENTAL AGENT MANAGER ============


class ElementalAgentManagerV16:
    """
    V16: Threshold Calibration Edition

    STRICT PRESERVATION:
    - Daily cycle counting
    - Water TLT inverse logic
    - Earth 3-loss entry blocking
    - Position cap €2,000
    - Trailing stop logic
    """

    COMMISSION_PCT = 0.0005
    SLIPPAGE_PCT = 0.001

    def __init__(self):
        self.earth_agent = EarthAgentV16()
        self.fire_agent = FireAgentV16()
        self.water_agent = WaterAgentV12()  # PRESERVED
        self.air_agent = AirAgentV12()  # PRESERVED
        self.ether_orchestrator = EtherOrchestratorV16()

        # Cycle counting (PRESERVED)
        self.total_cycles = 0
        self.consensus_count = 0
        self.execute_count = 0
        self.position_review_exits = 0

        self.agent_confidence_history: Dict[str, List[float]] = {
            "fire": [],
            "water": [],
            "air": [],
            "earth": [],
            "ether": [],
        }

        self.symbol_position_sizes: Dict[str, List[float]] = defaultdict(list)

    def increment_cycle(self):
        """V16: Daily cycle increment (PRESERVED)"""
        self.total_cycles += 1

    def is_symbol_available(self, symbol: str, cycle_date) -> bool:
        if symbol in IPO_DATES:
            ipo_date = datetime.strptime(IPO_DATES[symbol], "%Y-%m-%d")
            if hasattr(cycle_date, "date"):
                cycle_date = cycle_date.date()
            if hasattr(ipo_date, "date"):
                ipo_date = ipo_date.date()
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
    ) -> Tuple[bool, str]:
        """V16: Enhanced position evaluation"""
        position_pnl_pct = (current_price - entry_price) / entry_price

        self.earth_agent.update_unrealized_pnl(symbol, position_pnl_pct)

        # 60-day hard limit
        entry_date = self.earth_agent.entry_dates.get(symbol)
        if entry_date:
            days_held = (current_date - entry_date).days
            if days_held >= self.earth_agent.MAX_HOLD_DAYS:
                return True, "time_based"

        # Trailing stop
        if self.earth_agent.check_trailing_stop(symbol, position_pnl_pct):
            return True, "trailing_profit_stop"

        # Update peak for Fire agent
        if symbol in self.fire_agent.peak_prices:
            if current_price > self.fire_agent.peak_prices[symbol]:
                self.fire_agent.peak_prices[symbol] = current_price

        peak_price = self.fire_agent.peak_prices.get(symbol, entry_price)
        drawdown_from_peak = (
            (peak_price - current_price) / peak_price if peak_price > 0 else 0
        )

        # Water regime shift (PRESERVED)
        entry_risk_on = self.water_agent.entry_macro_score.get(symbol, 0.5)
        current_risk_on = macro_signal.risk_on_score

        if symbol in BOND_SYMBOLS:
            if current_risk_on > entry_risk_on + 0.20:
                return True, "water_bond_regime_shift"

        # Earth stop-loss
        if drawdown_from_peak > 0.15 and position_pnl_pct < 0:
            return True, f"earth_stop_{drawdown_from_peak:.1%}"

        # Fire volatility exit
        prices = list(self.fire_agent.price_history.get(symbol, []))
        if len(prices) >= 20:
            returns = [
                (prices[i] - prices[i - 1]) / prices[i - 1]
                for i in range(1, len(prices))
            ]
            vol = statistics.stdev(returns) if len(returns) > 1 else 0.02

            if vol > 0.04 and position_pnl_pct < -0.05:
                return True, f"fire_vol_exit_{vol:.2f}"

        return False, ""

    def process_entry_evaluation(
        self,
        symbol: str,
        current_price: float,
        portfolio_value: float,
        cycle_date: datetime,
        prana_level: float = 85.0,
    ) -> Optional[Dict]:
        """V16: Process entry evaluation"""
        self.fire_agent.record_price(symbol, current_price)
        self.air_agent.update_price(symbol, current_price)

        return self._evaluate_entry(
            symbol, current_price, portfolio_value, cycle_date, prana_level
        )

    def _evaluate_entry(
        self,
        symbol: str,
        current_price: float,
        portfolio_value: float,
        cycle_date: datetime,
        prana_level: float = 85.0,
    ) -> Optional[Dict]:
        """V16: Core entry evaluation"""
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
        """Get agent statistics"""
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

        return stats
