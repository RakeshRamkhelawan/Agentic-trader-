"""
Elemental Agent Manager V14 - CYCLE RESTORATION

V14 Key Changes:
- Cycle counting: Incremented PER DAY in engine (not per symbol)
- Earth: Revert threshold to 3 consecutive losses (was 2 in V13)
- Goal: Restore cycles to V10 level (~4,000) while keeping quality improvements

Retained from V12/V13:
- Water: TLT/Bond inverse logic (working correctly)
- Fire: ATR-based position sizing
- Hedge pairs: SH, PSQ, RWM, TBF infrastructure
"""

import os
import sys
import math
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque, defaultdict
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ElementalAgentsV14")


# ============ V10: NAVAGRAHA RISK MULTIPLIERS ============
PLANET_RISK_MULTIPLIERS = {
    "SUN":     1.00, "MOON":    0.80, "MARS":    1.40,
    "MERCURY": 0.90, "JUPITER": 1.20, "VENUS":   1.10,
    "SATURN":  0.60, "RAHU":    0.70, "KETU":    0.75,
}

# V10: Lagere thresholds voor hogere execute rate (12-20% target)
PLANET_THRESHOLDS = {
    "SUN":     0.55, "MOON":    0.53, "MARS":    0.60,
    "MERCURY": 0.54, "JUPITER": 0.57, "VENUS":   0.54,
    "SATURN":  0.50, "RAHU":    0.62, "KETU":    0.58,
}

ASSET_CLASSES = {
    "crypto": ["BTC", "ETH", "SOL", "AVAX", "LINK", "DOT", "ADA", "XRP",
               "DOGE", "LTC", "ATOM", "ALGO", "VET", "TRX", "XLM", "UNI",
               "MATIC", "AAVE", "FIL", "ETC"],
    "equity_us": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMZN", "TSLA",
                   "AMD", "CRM", "ADBE", "NFLX", "ORCL", "INTC", "PYPL", "ROKU", "ZM",
                   "COIN", "SNOW", "UBER", "IBM"],
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
    "crypto": 0.72, "equity_us": 0.85, "equity_eu": 0.78, "etf": 0.88,
}

# IPO dates for survivorship bias mitigation
IPO_DATES = {
    "COIN": "2021-04-14",
    "SNOW": "2020-09-16",
    "UBER": "2019-05-10",
    "ZM":   "2019-04-18",
    "ROKU": "2017-09-28",
}


@dataclass
class MacroSignal:
    risk_on_score: float
    regime: str


# ============ V14: EARTH AGENT - 3 LOSS THRESHOLD ============

class EarthAgentV14:
    """Earth Agent with V14 threshold: 3 consecutive losses"""
    
    def __init__(self):
        self.symbol_memory: Dict[str, deque] = defaultdict(lambda: deque(maxlen=20))
        self.win_rates: Dict[str, float] = {}
        
    def record_entry(self, symbol: str, entry_date: datetime):
        """Record entry for tracking"""
        pass
        
    def record_exit(self, symbol: str, pnl: float, win: bool):
        """Record trade outcome"""
        self.symbol_memory[symbol].append({
            'pnl': pnl,
            'win': win,
            'timestamp': datetime.now()
        })
        
        # Update win rate
        history = list(self.symbol_memory[symbol])
        if history:
            wins = sum(1 for h in history if h['win'])
            self.win_rates[symbol] = wins / len(history)
    
    def should_enter(self, symbol: str) -> bool:
        """
        V14: Block entry if 3 consecutive losses (balanced between V12's 4 and V13's 2)
        """
        recent = list(self.symbol_memory.get(symbol, []))
        if len(recent) >= 3:
            # Check last 3 trades
            last_three = recent[-3:]
            if all(not t['win'] for t in last_three):
                return False
        return True
    
    def calculate_confidence(self, symbol: str) -> float:
        """Calculate Earth confidence based on symbol's track record"""
        history = list(self.symbol_memory.get(symbol, []))
        if not history:
            return 0.85  # Default for new symbols
        
        wins = sum(1 for h in history if h['win'])
        win_rate = wins / len(history)
        
        # Recent momentum (last 5 trades)
        recent = history[-5:]
        recent_wins = sum(1 for h in recent if h['win'])
        recent_rate = recent_wins / len(recent) if recent else 0.5
        
        # Weighted confidence
        confidence = 0.6 * win_rate + 0.4 * recent_rate
        return min(0.95, max(0.55, confidence))


# ============ V12: FIRE AGENT - ATR POSITION SIZING ============

class FireAgentV12:
    """Fire Agent with V9 ATR sizing + peak tracking"""
    
    def __init__(self):
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
        self.entry_prices: Dict[str, float] = {}
        self.peak_prices: Dict[str, float] = {}
        self.max_position_pct = 0.10
        
    def record_price(self, symbol: str, price: float):
        """Record price update"""
        self.price_history[symbol].append(price)
    
    def record_entry(self, symbol: str, entry_price: float):
        """Record entry"""
        self.entry_prices[symbol] = entry_price
        self.peak_prices[symbol] = entry_price
    
    def record_exit(self, symbol: str, pnl: float):
        """Record exit"""
        self.entry_prices.pop(symbol, None)
        self.peak_prices.pop(symbol, None)
    
    def _calculate_atr(self, symbol: str, period: int = 14) -> float:
        """Calculate Average True Range"""
        prices = list(self.price_history.get(symbol, []))
        if len(prices) < period + 1:
            return 0.02  # Default 2%
        
        tr_list = []
        for i in range(1, min(period + 1, len(prices))):
            high = prices[-i]
            low = prices[-i-1]
            tr = abs(high - low) / low if low > 0 else 0
            tr_list.append(tr)
        
        return statistics.mean(tr_list) if tr_list else 0.02
    
    def calculate_position_size(self, symbol: str, portfolio_value: float,
                               harmony: float, dominant_planet: str) -> float:
        """V9: ATR-based position sizing"""
        prices = list(self.price_history.get(symbol, []))
        if len(prices) < 20:
            return portfolio_value * 0.01
        
        atr = self._calculate_atr(symbol)
        vol_factor = max(0.5, min(2.0, 0.03 / (atr + 0.001)))
        
        harmony_factor = 0.8 + (harmony * 0.4)
        
        streak = 0
        history = list(self.price_history.get(symbol, []))
        for i in range(1, min(6, len(history))):
            if history[-i] > history[-i-1]:
                streak += 1
            else:
                break
        streak_factor = 1.0 + (streak * 0.05)
        
        planet_mult = PLANET_RISK_MULTIPLIERS.get(dominant_planet, 1.0)
        
        base_pct = 0.015
        position_pct = base_pct * vol_factor * harmony_factor * streak_factor * planet_mult
        
        return portfolio_value * position_pct
    
    def calculate_confidence(self, symbol: str) -> float:
        """Calculate Fire confidence based on price momentum"""
        prices = list(self.price_history.get(symbol, []))
        if len(prices) < 20:
            return 0.70
        
        # Volatility regime
        returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                  for i in range(1, len(prices))]
        vol = statistics.stdev(returns) if len(returns) > 1 else 0.02
        
        if vol < 0.015:
            vol_conf = 0.75
        elif vol < 0.025:
            vol_conf = 0.60
        else:
            vol_conf = 0.45
        
        # Trend
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
        
        return min(0.85, max(0.50, 0.5 * vol_conf + 0.5 * trend_conf))


# ============ V12: WATER AGENT - BOND INVERSE + HEDGE SIGNALS ============

class WaterAgentV12:
    """Water Agent with bond inverse logic + hedge pair signals"""
    
    def __init__(self):
        self.ASSET_CLASSES = ASSET_CLASSES
        self.entry_macro_score: Dict[str, float] = {}
    
    def record_entry(self, symbol: str, macro_signal: MacroSignal):
        """V12: Record entry macro state"""
        self.entry_macro_score[symbol] = macro_signal.risk_on_score
    
    def record_exit(self, symbol: str):
        """V12: Clear entry memory"""
        self.entry_macro_score.pop(symbol, None)
    
    def _get_asset_class(self, symbol: str) -> str:
        for cls, syms in self.ASSET_CLASSES.items():
            if symbol in syms:
                return cls
        return "equity_us"
    
    def get_macro_signal(self, prices: List[float]) -> MacroSignal:
        """V12: Generate macro signal"""
        if len(prices) < 20:
            return MacroSignal(risk_on_score=0.5, regime="neutral")
        
        price_change_30d = (prices[-1] - prices[-min(30, len(prices))]) / prices[-min(30, len(prices))]
        
        advancing = sum(1 for i in range(1, min(20, len(prices))) if prices[-i] > prices[-i-1])
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
    
    def get_hedge_signal(self, primary_symbol: str, macro_signal: MacroSignal) -> Tuple[Optional[str], float]:
        """
        V12: Bepaalt of de hedge-tegenhanger aantrekkelijk is.
        Retourneert (hedge_symbol, hedge_confidence) of (None, 0).
        """
        hedge_sym = HEDGE_PAIRS.get(primary_symbol)
        if not hedge_sym:
            return None, 0.0
        
        risk_on = macro_signal.risk_on_score
        
        # V12: Alleen hedge activeren bij duidelijk risk-off signaal
        if risk_on < 0.35:
            # Lage confidence = klein mandaat voor hedge
            hedge_conf = 0.70 + (0.35 - risk_on) * 0.5
            return hedge_sym, min(hedge_conf, 0.85)
        
        return None, 0.0
    
    def calculate_confidence(self, symbol: str, macro_signal: MacroSignal) -> float:
        """
        V12: Confidence with macro regime awareness
        Inverse ETFs krijgen inverse macro-logica: hoog vertrouwen bij risk-off
        """
        # V12: Inverse ETFs - confidence stijgt als markt risk-off gaat
        if symbol in INVERSE_ETFS:
            risk_on = macro_signal.risk_on_score
            # Inverse ETF confidence stijgt als markt risk-off gaat
            base = WARM_START_CONFIDENCE.get("etf", 0.88)
            # Max confidence ~0.90 bij risk_on = 0.0
            return min(0.90, base * (1.5 - risk_on))
        
        # Normale confidence
        asset_class = self._get_asset_class(symbol)
        base_conf = WARM_START_CONFIDENCE.get(asset_class, 0.80)
        
        if macro_signal.regime == "expansion":
            confidence = base_conf * 1.05
        elif macro_signal.regime == "contraction":
            confidence = base_conf * 0.85
        else:
            confidence = base_conf
        
        return min(0.95, max(0.60, confidence))


# ============ V12: AIR AGENT - MOMENTUM + SENTIMENT ============

class AirAgentV12:
    """Air Agent with momentum-based confidence"""
    
    def __init__(self):
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=30))
        self.sentiment_cache: Dict[str, Dict] = {}
    
    def update_price(self, symbol: str, price: float):
        """Update price history"""
        self.price_history[symbol].append(price)
    
    def calculate_confidence(self, symbol: str, current_date: datetime = None) -> float:
        """Calculate Air confidence based on momentum"""
        prices = list(self.price_history.get(symbol, []))
        if len(prices) < 10:
            return 0.60
        
        # Simple RSI-like calculation
        gains = []
        losses = []
        for i in range(1, min(15, len(prices))):
            change = prices[-i] - prices[-i-1]
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


# ============ V12: ETHER ORCHESTRATOR ============

class EtherOrchestratorV12:
    """Ether - consensus synthesis with V10 thresholds"""
    
    AGENT_WEIGHTS = {
        "fire": 0.30, "earth": 0.25, "water": 0.20, "air": 0.15, "ether": 0.10
    }
    
    def synthesize(self, fire_conf: float, water_conf: float,
                   air_conf: float, earth_conf: float) -> Tuple[float, bool]:
        """Synthesize agent confidences into harmony score"""
        
        weighted_harmony = (
            fire_conf * self.AGENT_WEIGHTS["fire"] +
            water_conf * self.AGENT_WEIGHTS["water"] +
            air_conf * self.AGENT_WEIGHTS["air"] +
            earth_conf * self.AGENT_WEIGHTS["earth"]
        )
        
        # Consensus: all agents must be above minimum threshold
        min_threshold = 0.50
        consensus = all([
            fire_conf >= min_threshold,
            water_conf >= min_threshold,
            air_conf >= min_threshold,
            earth_conf >= min_threshold
        ])
        
        return weighted_harmony, consensus
    
    def should_execute(self, harmony: float, consensus: bool, 
                       dominant_planet: str) -> bool:
        """Determine if trade should execute based on harmony and planet"""
        threshold = PLANET_THRESHOLDS.get(dominant_planet, 0.55)
        return consensus and harmony >= threshold


# ============ V14: ELEMENTAL AGENT MANAGER ============

class ElementalAgentManagerV14:
    """
    V14: Cycle restoration - daily increment outside symbol loop
    """
    
    COMMISSION_PCT = 0.0005
    SLIPPAGE_PCT = 0.001
    
    def __init__(self):
        self.earth_agent = EarthAgentV14()
        self.fire_agent = FireAgentV12()
        self.water_agent = WaterAgentV12()
        self.air_agent = AirAgentV12()
        self.ether_orchestrator = EtherOrchestratorV12()
        
        # V14: Cycle counting - incremented by engine PER DAY
        self.total_cycles = 0
        self.consensus_count = 0
        self.execute_count = 0
        self.position_review_exits = 0
        
        self.agent_confidence_history: Dict[str, List[float]] = {
            "fire": [], "water": [], "air": [], "earth": [], "ether": []
        }
        
        self.symbol_position_sizes: Dict[str, List[float]] = defaultdict(list)
    
    def increment_cycle(self):
        """
        V14: Called by engine once per trading day (outside symbol loop)
        This restores V10's cycle counting behavior
        """
        self.total_cycles += 1
    
    def is_symbol_available(self, symbol: str, cycle_date) -> bool:
        """V10: Check if symbol was listed on cycle_date"""
        if symbol in IPO_DATES:
            ipo_date = datetime.strptime(IPO_DATES[symbol], "%Y-%m-%d")
            # Handle both datetime and date objects
            if hasattr(cycle_date, 'date'):
                cycle_date = cycle_date.date()
            if hasattr(ipo_date, 'date'):
                ipo_date = ipo_date.date()
            return cycle_date >= ipo_date
        return True
    
    def record_trade_outcome(self, symbol: str, pnl: float, win: bool):
        """V10: Feedback dispatch"""
        self.earth_agent.record_exit(symbol, pnl, win)
        self.fire_agent.record_exit(symbol, pnl)
        self.water_agent.record_exit(symbol)
    
    def evaluate_open_position(self, symbol: str, current_price: float,
                               macro_signal: MacroSignal, current_date: datetime) -> Tuple[bool, str]:
        """
        V12: Position review with calibrated Water/Earth/Vol exits
        Returns (should_exit, reason)
        """
        entry_price = self.fire_agent.entry_prices.get(symbol)
        if not entry_price:
            return False, ""
        
        position_pnl_pct = (current_price - entry_price) / entry_price
        
        # Update peak
        if current_price > self.fire_agent.peak_prices.get(symbol, entry_price):
            self.fire_agent.peak_prices[symbol] = current_price
        
        peak_price = self.fire_agent.peak_prices.get(symbol, entry_price)
        drawdown_from_peak = (peak_price - current_price) / peak_price if peak_price > 0 else 0
        
        # Water: Exit if regime shift against position
        entry_risk_on = self.water_agent.entry_macro_score.get(symbol, 0.5)
        current_risk_on = macro_signal.risk_on_score
        
        # Check if symbol is a bond
        if symbol in BOND_SYMBOLS:
            # Bonds: exit if risk-on increases significantly
            if current_risk_on > entry_risk_on + 0.20:
                return True, f"water_bond_regime_shift ({current_risk_on:.2f} > {entry_risk_on:.2f})"
        
        # Standard exit logic
        if drawdown_from_peak > 0.15 and position_pnl_pct < 0:
            return True, f"earth_stop_{drawdown_from_peak:.1%}"
        
        # Fire: Volatility-based exit
        prices = list(self.fire_agent.price_history.get(symbol, []))
        if len(prices) >= 20:
            returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                      for i in range(1, len(prices))]
            vol = statistics.stdev(returns) if len(returns) > 1 else 0.02
            
            if vol > 0.04 and position_pnl_pct < -0.05:
                return True, f"fire_vol_exit_{vol:.2f}"
        
        return False, ""
    
    def process_entry_evaluation(self, symbol: str, current_price: float,
                                 portfolio_value: float, cycle_date: datetime,
                                 prana_level: float = 85.0) -> Optional[Dict]:
        """
        V14: Process entry evaluation - NO cycle counting here
        (Cycle is incremented once per day by engine)
        """
        self.fire_agent.record_price(symbol, current_price)
        self.air_agent.update_price(symbol, current_price)
        
        return self._evaluate_entry(symbol, current_price, portfolio_value, cycle_date, prana_level)
    
    def _evaluate_entry(self, symbol: str, current_price: float,
                       portfolio_value: float, cycle_date: datetime,
                       prana_level: float = 85.0) -> Optional[Dict]:
        """V14: Core entry evaluation logic"""
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
        
        if not self.ether_orchestrator.should_execute(harmony, consensus, dominant_planet):
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
                    "samples": len(confidences)
                }
        
        stats["consensus_achieved_pct"] = (self.consensus_count / self.total_cycles * 100) if self.total_cycles > 0 else 0
        stats["execute_rate_pct"] = (self.execute_count / self.total_cycles * 100) if self.total_cycles > 0 else 0
        stats["total_cycles"] = self.total_cycles
        stats["consensus_count"] = self.consensus_count
        stats["execute_count"] = self.execute_count
        stats["position_review_exits"] = self.position_review_exits
        
        return stats
