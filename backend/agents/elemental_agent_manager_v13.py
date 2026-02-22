"""
Elemental Agent Manager V13 - CYCLE FIX + COIN THRESHOLD FIX

V13 Key Changes:
- Earth: should_enter() threshold lowered from 4 to 2 consecutive losses
- Water: TLT/Bond inverse logica retained (working correctly)
- Engine: Fixed elemental cycles counting (outside symbol loop)
- Baseline: V12 without cycle crash bug

V12 issues fixed:
- Elemental cycles crashed from 4,427 to 1,368 (-69%)
- Earth COIN threshold too high (4 losses for asset with only 6 trades)
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
logger = logging.getLogger("ElementalAgentsV13")


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


# ============ V12: EARTH AGENT - CALIBRATED EXIT + ENTRY BLOCK ============

class EarthAgentV12:
    """Earth Agent with calibrated position review + entry blocking"""
    
    def __init__(self):
        self.symbol_memory: Dict[str, deque] = defaultdict(lambda: deque(maxlen=20))
        self.win_rates: Dict[str, float] = {}
        
        # V12: Entry tracking with dates
        self.entry_confidences: Dict[str, float] = {}
        self.entry_dates: Dict[str, datetime] = {}
    
    def record_entry(self, symbol: str, entry_date: datetime):
        """V12: Record entry for position review"""
        self.entry_confidences[symbol] = self.calculate_confidence(symbol)
        self.entry_dates[symbol] = entry_date
    
    def record_exit(self, symbol: str, pnl: float, win: bool):
        """V12: Record exit and clear entry memory"""
        self.symbol_memory[symbol].append({"pnl": pnl, "win": win, "timestamp": datetime.utcnow()})
        self.entry_confidences.pop(symbol, None)
        self.entry_dates.pop(symbol, None)
    
    def should_enter(self, symbol: str) -> bool:
        """
        V13: Earth blokkeert entry als recente performance slecht is.
        Drempel verlaagd van 4 naar 2 opeenvolgende verliezen.
        """
        recent = list(self.symbol_memory.get(symbol, []))
        # V13: Lower threshold - 2 consecutive losses blocks entry
        if len(recent) >= 2:
            # Check laatste 2 trades - beide verlies?
            if not recent[-1]["win"] and not recent[-2]["win"]:
                return False  # 2 opeenvolgende verliezen → Earth vertrouwt niet
        return True
    
    def evaluate_open_position(self, symbol: str, current_date: datetime) -> str:
        """
        V12: Earth herbeoordeelt open positie
        - Minimum 5 dagen holding voordat review actief wordt
        - EXIT drempel: 0.60 (40% daling vereist)
        """
        if symbol not in self.entry_confidences or symbol not in self.entry_dates:
            return "HOLD"
        
        # V12: Minimum 5 dagen holding
        entry_date = self.entry_dates[symbol]
        days_held = (current_date - entry_date).days
        if days_held < 5:
            return "HOLD"
        
        entry_conf = self.entry_confidences[symbol]
        current_conf = self.calculate_confidence(symbol)
        
        # V12: Strengere drempel: 0.60 (40% daling vereist)
        if current_conf < entry_conf * 0.60:
            return "EXIT"
        return "HOLD"
    
    def _get_asset_class(self, symbol: str) -> str:
        for cls, symbols in ASSET_CLASSES.items():
            if symbol in symbols:
                return cls
        return "equity_us"
    
    def calculate_confidence(self, symbol: str) -> float:
        """Adaptive confidence based on historical performance"""
        history = self.symbol_memory[symbol]
        asset_class = self._get_asset_class(symbol)
        
        if len(history) < 5:
            return WARM_START_CONFIDENCE.get(asset_class, 0.80)
        
        recent_win_rate = sum(1 for t in history if t["win"]) / len(history)
        avg_pnl = sum(t["pnl"] for t in history) / len(history)
        
        base = 0.4 + (recent_win_rate * 0.5)
        pnl_factor = min(max(avg_pnl / 100, -0.15), 0.15)
        
        confidence = base + pnl_factor
        warm_start = WARM_START_CONFIDENCE.get(asset_class, 0.80)
        blended = (confidence * 0.7) + (warm_start * 0.3)
        
        return min(max(blended, 0.40), 0.95)


# ============ V12: FIRE AGENT - CALIBRATED EXIT ============

class FireAgentV12:
    """Fire Agent with calibrated position review"""
    
    def __init__(self):
        self.loss_streaks: Dict[str, int] = defaultdict(int)
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
        self.PLANET_MULTIPLIERS = PLANET_RISK_MULTIPLIERS
        
        # V10: Entry tracking
        self.entry_atr: Dict[str, float] = {}
        self.position_peaks: Dict[str, float] = {}
    
    def record_price(self, symbol: str, price: float):
        """V10: Record price for all symbols"""
        self.price_history[symbol].append(price)
    
    def record_entry(self, symbol: str, entry_price: float):
        """V10: Record entry for position review"""
        self.entry_atr[symbol] = self.calculate_atr_pct(symbol)
        self.position_peaks[symbol] = entry_price
    
    def update_peak(self, symbol: str, current_price: float):
        """V10: Update peak price for open position"""
        if symbol in self.position_peaks:
            self.position_peaks[symbol] = max(self.position_peaks[symbol], current_price)
    
    def record_exit(self, symbol: str, pnl: float):
        """V10: Record exit and clear entry memory"""
        self.record_outcome(symbol, pnl)
        self.entry_atr.pop(symbol, None)
        self.position_peaks.pop(symbol, None)
    
    def record_outcome(self, symbol: str, pnl: float):
        """Record trade outcome"""
        if pnl < 0:
            self.loss_streaks[symbol] += 1
        else:
            self.loss_streaks[symbol] = 0
    
    def calculate_atr_pct(self, symbol: str) -> float:
        """Calculate ATR as percentage"""
        prices = list(self.price_history[symbol])
        if len(prices) < 5:
            return 0.03
        changes = [abs(prices[i] / prices[i-1] - 1) for i in range(1, len(prices))]
        return statistics.mean(changes)
    
    def calculate_confidence(self, symbol: str) -> float:
        """V10: Confidence with streak and volatility penalties"""
        streak = self.loss_streaks[symbol]
        atr_pct = self.calculate_atr_pct(symbol)
        
        streak_penalty = min(streak * 0.08, 0.45)
        vol_penalty = min(atr_pct / 0.05, 0.30)
        
        confidence = 0.92 - streak_penalty - vol_penalty
        return max(confidence, 0.37)
    
    def evaluate_open_position(self, symbol: str, current_price: float) -> str:
        """
        V10: Fire evalueert volatiliteitsexplosie en peak-drawdown
        - Minimum 10 dagen price history voor stabiele ATR
        - vol_ratio > 4.0 (was 2.5/3.0) + drawdown < -15%
        - vol_ratio > 6.0 (was 4.0/5.0)
        """
        if symbol not in self.entry_atr:
            return "HOLD"
        
        # V10: Wacht tot price_history >= 10 entries
        if len(self.price_history[symbol]) < 10:
            return "HOLD"
        
        entry_atr = self.entry_atr[symbol]
        current_atr = self.calculate_atr_pct(symbol)
        peak_price = self.position_peaks.get(symbol, current_price)
        
        vol_ratio = current_atr / max(entry_atr, 0.001)
        peak_drawdown = (current_price / peak_price) - 1
        
        # V10: Verhoogde drempels
        if vol_ratio > 4.0 and peak_drawdown < -0.15:
            return "EXIT"
        if vol_ratio > 6.0:
            return "EXIT"
        return "HOLD"
    
    def calculate_position_size(self, symbol: str, portfolio_value: float,
                               harmony: float, dominant_planet: str) -> float:
        """
        V10: Fire position sizing - ONGEWIJZIGD van v8/v9
        """
        atr_pct = self.calculate_atr_pct(symbol)
        streak = self.loss_streaks[symbol]
        
        vol_factor = 1.0 / (1.0 + atr_pct * 6)
        harmony_factor = harmony ** 2
        streak_factor = 0.5 ** streak
        planet_mult = self.PLANET_MULTIPLIERS.get(dominant_planet, 1.0)
        
        base_pct = 0.015
        position_pct = base_pct * vol_factor * harmony_factor * streak_factor * planet_mult
        
        return portfolio_value * position_pct


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
        
        return min(confidence, 0.90)
    
    def evaluate_open_position(self, symbol: str, macro_signal: MacroSignal) -> str:
        """
        V12: Water evalueert regime-shift
        - Bonds: inverse relatie (risk-on stijging = exit)
        - Crypto: 0.35, Equity: 0.50
        """
        if symbol not in self.entry_macro_score:
            return "HOLD"
        
        entry_risk_on = self.entry_macro_score[symbol]
        current_risk_on = macro_signal.risk_on_score
        
        # V12: Bonds - inverse relatie
        if symbol in BOND_SYMBOLS:
            # Exit bij risk-on stijging (omgekeerde logica vs. aandelen)
            if (current_risk_on - entry_risk_on) > 0.20:
                return "EXIT"
            return "HOLD"
        
        # Normale assets
        asset_class = self._get_asset_class(symbol)
        shift_threshold = 0.35 if asset_class == "crypto" else 0.50
        
        if (entry_risk_on - current_risk_on) > shift_threshold:
            return "EXIT"
        return "HOLD"


# ============ V12: AIR AGENT - TECHNICAL + SENTIMENT ============

class AirAgentV12:
    """Air Agent - technical signals + optional LLM sentiment"""
    
    def __init__(self):
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        
        # V12: Sentiment cache (optioneel)
        self.sentiment_cache: Dict[str, Dict] = {}
        # Structuur: { symbol: { 'score': float, 'date': datetime, 'source': str } }
        # Score: -1.0 (sterk negatief) → +1.0 (sterk positief)
    
    def update_price(self, symbol: str, price: float):
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=50)
        self.price_history[symbol].append(price)
    
    def inject_sentiment(self, symbol: str, score: float, date: datetime, source: str = 'llm'):
        """
        V12: Externe feed injecteert sentiment score.
        Kan worden aangeroepen door LLM-pipeline, news scraper, of FinGPT.
        Als niet aangeroepen: sentiment = 0.0 (neutraal, geen effect).
        """
        self.sentiment_cache[symbol] = {
            'score': max(-1.0, min(1.0, score)),
            'date': date,
            'source': source
        }
    
    def get_sentiment_for_date(self, symbol: str, date: datetime) -> float:
        """
        V12: Voor backtesting - gebruik historische sentiment als beschikbaar.
        Geeft 0.0 (neutraal) terug als geen data — geen lookahead.
        """
        sent = self.sentiment_cache.get(symbol)
        if sent and sent['date'] <= date:
            # Check if not too old (< 7 days)
            if (date - sent['date']).days <= 7:
                return sent['score']
        return 0.0
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
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
    
    def calculate_confidence(self, symbol: str, current_date: Optional[datetime] = None) -> float:
        """
        V12: Air's confidence combineert momentum (80%) met sentiment (20%).
        Als geen sentiment beschikbaar: puur momentum zoals voorheen.
        """
        prices = list(self.price_history.get(symbol, []))
        
        if len(prices) < 20:
            momentum_conf = 0.60
        else:
            rsi = self._calculate_rsi(prices)
            ema20 = sum(prices[-20:]) / 20
            ema50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else ema20
            
            trend_up = ema20 > ema50
            
            if trend_up and rsi < 70:
                momentum_conf = 0.75
            elif not trend_up and rsi > 30:
                momentum_conf = 0.55
            elif rsi < 35:
                momentum_conf = 0.60
            elif rsi > 65:
                momentum_conf = 0.45
            else:
                momentum_conf = 0.55
        
        # V12: Sentiment component (optioneel)
        if current_date:
            sentiment_score = self.get_sentiment_for_date(symbol, current_date)
            # Sentiment score -1..+1 → confidence bijdrage -0.10..+0.10
            sentiment_boost = sentiment_score * 0.10
            return max(0.45, min(0.95, momentum_conf + sentiment_boost))
        
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
        
        values = [fire_conf, water_conf, air_conf, earth_conf]
        spread = max(values) - min(values)
        disagreement_penalty = spread * 0.05
        
        harmony = weighted_harmony - disagreement_penalty
        harmony = min(max(harmony, 0.0), 1.0)
        
        min_threshold = 0.35
        agents_above = sum(1 for c in values if c >= min_threshold)
        consensus = agents_above >= 4
        
        return harmony, consensus
    
    def should_execute(self, harmony: float, consensus: bool,
                       dominant_planet: str) -> bool:
        """Execute decision based on V10 planet threshold"""
        threshold = PLANET_THRESHOLDS.get(dominant_planet, 0.55)
        return consensus and harmony >= threshold


# ============ V12: MAIN MANAGER ============

class ElementalAgentManagerV13:
    """V12: Hedge Pairs + Bond Inverse + Sentiment (optional)"""
    
    SLIPPAGE_PCT = 0.001
    COMMISSION_PCT = 0.0005
    
    def __init__(self):
        self.fire_agent = FireAgentV12()
        self.water_agent = WaterAgentV12()
        self.air_agent = AirAgentV12()
        self.earth_agent = EarthAgentV12()
        self.ether_orchestrator = EtherOrchestratorV12()
        
        self.agent_confidence_history: Dict[str, List[float]] = {
            "fire": [], "water": [], "air": [], "earth": [], "ether": []
        }
        self.consensus_count = 0
        self.total_cycles = 0
        self.execute_count = 0
        self.position_review_exits = 0
    
    def is_symbol_available(self, symbol: str, cycle_date: datetime) -> bool:
        """V10: Check if symbol was listed on cycle_date"""
        if symbol in IPO_DATES:
            ipo_date = datetime.strptime(IPO_DATES[symbol], "%Y-%m-%d")
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
        V10: Position Review Loop with calibrated sensitivity
        Returns: (should_exit, reason)
        """
        self.fire_agent.update_peak(symbol, current_price)
        
        earth_exit = self.earth_agent.evaluate_open_position(symbol, current_date)
        fire_exit = self.fire_agent.evaluate_open_position(symbol, current_price)
        water_exit = self.water_agent.evaluate_open_position(symbol, macro_signal)
        
        if earth_exit == "EXIT":
            return True, "earth_confidence_drop"
        if fire_exit == "EXIT":
            return True, "fire_vol_explosion"
        if water_exit == "EXIT":
            return True, "water_regime_shift"
        
        return False, "hold"
    
    def process_entry_cycle(self, symbol: str, current_price: float,
                           portfolio_value: float, cycle_date: datetime,
                           prana_level: float = 85.0) -> Optional[Dict]:
        """V13: Process entry evaluation WITH cycle counting"""
        self.fire_agent.record_price(symbol, current_price)
        self.air_agent.update_price(symbol, current_price)
        
        self.total_cycles += 1
        
        return self._evaluate_entry(symbol, current_price, portfolio_value, cycle_date, prana_level)
    
    def process_entry_cycle(self, symbol: str, current_price: float,
                           portfolio_value: float, cycle_date: datetime,
                           prana_level: float = 85.0) -> Optional[Dict]:
        """V13: Process entry evaluation WITH cycle counting (V10/V12 style)"""
        self.fire_agent.record_price(symbol, current_price)
        self.air_agent.update_price(symbol, current_price)
        
        # V13: Count cycles HERE (consistent with V10/V12)
        self.total_cycles += 1
        
        return self._evaluate_entry(symbol, current_price, portfolio_value, cycle_date, prana_level)
    
    def _evaluate_entry(self, symbol: str, current_price: float,
                       portfolio_value: float, cycle_date: datetime,
                       prana_level: float = 85.0) -> Optional[Dict]:
        """V13: Core entry evaluation logic"""
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
