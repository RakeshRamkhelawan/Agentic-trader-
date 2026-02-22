"""
Elemental Agent Manager V17 - VedAstro Hybrid Edition

Combines VedAstro TradingSignalGenerator with Elemental risk management.

V17 Key Changes:
1. VedAstro-driven entry decisions (BUY/SELL/HOLD)
2. Elemental simplified to risk filtering only
3. Fire: Position sizing only (€2k cap)
4. Earth: Entry blocking only (3-loss rule)
5. Water: Regime check preserved
6. Aggressive thresholds: Fire 0.30, Earth 0.40

Retained from V16:
- Daily cycle counting (5,239 cycles)
- Trailing stop (+40% → -15%)
- 60-day failsafe
- €2,000 position cap
- Water TLT inverse logic
"""

import os
import sys
import math
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ElementalAgentsV17")


# ============ V17: NAVAGRAHA RISK MULTIPLIERS (Preserved) ============
PLANET_RISK_MULTIPLIERS = {
    "SUN":     1.00, "MOON":    0.80, "MARS":    1.40,
    "MERCURY": 0.90, "JUPITER": 1.20, "VENUS":   1.10,
    "SATURN":  0.60, "RAHU":    0.70, "KETU":    0.75,
}

# V17: Aggressive thresholds for higher execution rate
PLANET_THRESHOLDS = {
    "SUN":     0.50,  # was 0.52
    "MOON":    0.48,  # was 0.50
    "MARS":    0.55,  # was 0.57
    "MERCURY": 0.49,  # was 0.51
    "JUPITER": 0.52,  # was 0.54
    "VENUS":    0.49, # was 0.51
    "SATURN":   0.45, # was 0.47
    "RAHU":     0.57, # was 0.59
    "KETU":     0.53, # was 0.55
}

ASSET_CLASSES = {
    "crypto": ["BTC", "ETH", "SOL", "AVAX", "LINK", "DOT", "ADA", "XRP",
               "DOGE", "LTC", "ATOM", "ALGO", "VET", "TRX", "XLM", "UNI",
               "MATIC", "FIL", "ETC"],  # AAVE removed
    "equity_us": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMZN", "TSLA",
                   "AMD", "CRM", "ADBE", "NFLX", "ORCL", "INTC", "PYPL", "ROKU", "ZM",
                   "COIN", "SNOW", "UBER", "IBM"],
    "equity_eu": ["ASML", "SAP", "AIR", "ROG", "NESN", "TTE", "SHEL"],
    "etf": ["SPY", "QQQ", "VTI", "IWM", "EEM", "EFA", "GLD", "TLT", "USO", "VIX"],
    "bond": ["TLT", "IEF", "AGG", "BND", "GOVT"],
    "inverse_etf": ["SH", "PSQ", "RWM", "TBF"],
}

HEDGE_PAIRS = {
    "SPY": "SH",
    "QQQ": "PSQ",
    "IWM": "RWM",
    "TLT": "TBF",
}

INVERSE_ETFS = {"SH", "PSQ", "RWM", "TBF"}
BOND_SYMBOLS = {"TLT", "IEF", "AGG", "BND", "TBF", "GOVT"}

WARM_START_CONFIDENCE = {
    "crypto": 0.72, "equity_us": 0.85, "equity_eu": 0.78, "etf": 0.88,
}

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


# ============ V17: FIRE AGENT - POSITION SIZING ONLY ============

class FireAgentV17:
    """
    V17: Fire Agent - ONLY position sizing, no confidence calculation.
    Harmony comes from VedAstro strength_score.
    """
    
    MAX_POSITION_EUR = 2000.0
    
    def __init__(self):
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
        self.entry_prices: Dict[str, float] = {}
        self.peak_prices: Dict[str, float] = {}
        
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
            low = prices[-i-1]
            tr = abs(high - low) / low if low > 0 else 0
            tr_list.append(tr)
        
        return statistics.mean(tr_list) if tr_list else 0.02
    
    def calculate_position_size(self, symbol: str, portfolio_value: float,
                               vedastro_score: float, dominant_planet: str) -> float:
        """
        V17: Position sizing using VedAstro score (0-100) as harmony.
        No confidence calculation - VedAstro provides the signal quality.
        """
        prices = list(self.price_history.get(symbol, []))
        
        if len(prices) < 20:
            base_pct = 0.01
        else:
            atr = self._calculate_atr(symbol)
            vol_factor = max(0.5, min(2.0, 0.03 / (atr + 0.001)))
            
            # VedAstro score (0-100) → harmony factor (0.5-1.2)
            harmony_factor = 0.5 + (vedastro_score / 100) * 0.7
            
            streak = 0
            for i in range(1, min(6, len(prices))):
                if prices[-i] > prices[-i-1]:
                    streak += 1
                else:
                    break
            streak_factor = 1.0 + (streak * 0.05)
            
            planet_mult = PLANET_RISK_MULTIPLIERS.get(dominant_planet, 1.0)
            
            base_pct = 0.015 * vol_factor * harmony_factor * streak_factor * planet_mult
        
        raw_size = portfolio_value * base_pct
        max_pct_size = portfolio_value * 0.02
        
        return min(raw_size, max_pct_size, self.MAX_POSITION_EUR)


# ============ V17: EARTH AGENT - ENTRY BLOCKING ONLY ============

class EarthAgentV17:
    """
    V17: Earth Agent - ONLY entry blocking and trailing stops.
    No confidence calculation - VedAstro provides signal quality.
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
        self.symbol_memory[symbol].append({
            'pnl': pnl,
            'win': win,
            'timestamp': datetime.now()
        })
        
        history = list(self.symbol_memory[symbol])
        if history:
            wins = sum(1 for h in history if h['win'])
            self.win_rates[symbol] = wins / len(history)
        
        self.entry_dates.pop(symbol, None)
        self.peak_unrealized_pnl.pop(symbol, None)
        self.trailing_stop_active.pop(symbol, None)
    
    def should_enter(self, symbol: str) -> bool:
        """V17: 3 consecutive losses entry blocking (preserved)"""
        recent = list(self.symbol_memory.get(symbol, []))
        if len(recent) >= 3:
            last_three = recent[-3:]
            if all(not t['win'] for t in last_three):
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
    
    def get_days_held(self, symbol: str, current_date: datetime) -> int:
        entry_date = self.entry_dates.get(symbol)
        if entry_date:
            return (current_date - entry_date).days
        return 0


# ============ V12: WATER AGENT (PRESERVED - DO NOT MODIFY) ============

class WaterAgentV12:
    """Water Agent - STRICTLY PRESERVED from V12/V16"""
    
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


# ============ V17: VEDASTRO ELEMENTAL AGENT (HYBRID) ============

class VedAstroElementalAgentV17:
    """
    V17: Hybrid agent combining VedAstro signal generation with Elemental risk management.
    
    Flow:
    1. VedAstro TradingSignalGenerator provides BUY/SELL/HOLD decision
    2. Elemental agents filter for risk (entry blocking, position sizing)
    3. Entry executed if VedAstro says BUY + Elemental risk filters pass
    """
    
    COMMISSION_PCT = 0.0005
    SLIPPAGE_PCT = 0.001
    MIN_VEDASTRO_CONFIDENCE = 50.0  # Minimum 50% confidence
    MIN_VEDASTRO_SCORE = 45.0  # Minimum strength score
    
    def __init__(self):
        # Import VedAstro components
        try:
            from backend.vedastro import EnhancedAstroOrchestrator, TradingSignalGenerator
            self.astro_orchestrator = EnhancedAstroOrchestrator()
            self.signal_generator = TradingSignalGenerator()
            self.vedastro_available = True
            logger.info("✅ VedAstro components loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load VedAstro: {e}")
            self.vedastro_available = False
            raise
        
        # Elemental risk components
        self.fire_agent = FireAgentV17()
        self.earth_agent = EarthAgentV17()
        self.water_agent = WaterAgentV12()
        
        # Cycle counting (preserved)
        self.total_cycles = 0
        self.consensus_count = 0
        self.execute_count = 0
        self.position_review_exits = 0
        self.vedastro_entries = 0  # NEW: Track VedAstro-driven entries
        
        self.agent_confidence_history: Dict[str, List[float]] = {
            "fire": [], "water": [], "air": [], "earth": [], "ether": []
        }
        
        self.symbol_position_sizes: Dict[str, List[float]] = defaultdict(list)
        self.astro_cache: Dict[str, Any] = {}  # Cache for VedAstro results
    
    def increment_cycle(self):
        """V17: Daily cycle increment (PRESERVED)"""
        self.total_cycles += 1
    
    def _get_cached_astro(self, symbol: str, date: datetime, price: float):
        """V17: Cache VedAstro calculations for performance"""
        cache_key = f"{symbol}_{date.strftime('%Y-%m-%d')}"
        
        if cache_key not in self.astro_cache:
            # Will be populated by evaluate_entry
            pass
        
        return self.astro_cache.get(cache_key)
    
    async def evaluate_entry(self, symbol: str, current_price: float,
                           cycle_date: datetime, portfolio_value: float) -> Optional[Dict]:
        """
        V17 Entry evaluation:
        1. Get VedAstro analysis (async)
        2. Filter: Only BUY signals with sufficient confidence
        3. Check Elemental risk filters
        4. Calculate position size using VedAstro score
        5. Return entry dict or None
        """
        if not self.vedastro_available:
            logger.warning("VedAstro not available, skipping entry")
            return None
        
        # 1. VEDASTRO ANALYSIS (async)
        try:
            cache_key = f"{symbol}_{cycle_date.strftime('%Y-%m-%d')}"
            
            if cache_key in self.astro_cache:
                astro_analysis = self.astro_cache[cache_key]
            else:
                astro_analysis = await self.astro_orchestrator.analyze_asset(
                    symbol=symbol,
                    current_price=current_price
                )
                self.astro_cache[cache_key] = astro_analysis
            
            signal = astro_analysis.trading_signal
            
        except Exception as e:
            logger.warning(f"VedAstro failed for {symbol}: {e}")
            return None
        
        # 2. FILTER: Only BUY signals
        signal_value = signal.signal
        if isinstance(signal_value, str):
            signal_str = signal_value.lower()
        else:
            # Handle enum
            signal_str = signal_value.value.lower() if hasattr(signal_value, 'value') else str(signal_value).lower()
        
        if signal_str not in ['buy', 'strong_buy']:
            return None
        
        # 3. FILTER: Minimum VedAstro confidence
        if signal.confidence < self.MIN_VEDASTRO_CONFIDENCE:
            return None
        
        if signal.strength_score < self.MIN_VEDASTRO_SCORE:
            return None
        
        # 4. ELEMENTAL RISK CHECKS
        # Check 4a: Earth entry blocking (3-loss rule preserved)
        if not self.earth_agent.should_enter(symbol):
            return None
        
        # Check 4b: Water regime compatibility (TLT logic preserved)
        prices = list(self.fire_agent.price_history.get(symbol, []))
        if len(prices) >= 20:
            macro_signal = self.water_agent.get_macro_signal(prices)
            
            # For bonds, check regime shift
            if symbol in BOND_SYMBOLS:
                entry_risk_on = self.water_agent.entry_macro_score.get(symbol, 0.5)
                if macro_signal.risk_on_score > entry_risk_on + 0.20:
                    return None  # Would trigger regime exit anyway
        
        # 5. POSITION SIZING (Fire agent with VedAstro score)
        dominant_planet = self._get_dominant_planet(cycle_date)
        position_size = self.fire_agent.calculate_position_size(
            symbol=symbol,
            portfolio_value=portfolio_value,
            vedastro_score=signal.strength_score,
            dominant_planet=dominant_planet
        )
        
        if position_size <= 0:
            return None
        
        # Track VedAstro entry
        self.vedastro_entries += 1
        self.execute_count += 1
        
        # 6. RETURN ENTRY DICT
        entry_price = current_price * (1 + self.SLIPPAGE_PCT)
        commission = position_size * self.COMMISSION_PCT
        actual_size = position_size - commission
        quantity = actual_size / entry_price
        
        if quantity <= 0:
            return None
        
        # Record entry for tracking
        self.earth_agent.record_entry(symbol, cycle_date)
        self.fire_agent.record_entry(symbol, entry_price)
        
        # Get macro for water
        if len(prices) >= 20:
            macro = self.water_agent.get_macro_signal(prices)
            self.water_agent.record_entry(symbol, macro)
        
        return {
            "symbol": symbol,
            "action": "BUY",
            "entry_price": entry_price,
            "quantity": quantity,
            "position_size": position_size,
            "vedastro_signal": signal_str,
            "vedastro_confidence": signal.confidence,
            "vedastro_strength": signal.strength_score,
            "vedastro_risk": signal.risk_level,
            "dasha_context": signal.dasha_context if hasattr(signal, 'dasha_context') else "",
            "primary_factors": signal.primary_factors if hasattr(signal, 'primary_factors') else [],
            "planet": dominant_planet,
        }
    
    def evaluate_open_position(self, symbol: str, current_price: float,
                              current_date: datetime, entry_price: float) -> Tuple[bool, str]:
        """
        V17: Enhanced position evaluation with VedAstro SELL signals.
        Preserved from V16: trailing stop, time-based, earth stop, fire vol exit.
        """
        position_pnl_pct = (current_price - entry_price) / entry_price
        
        # Update trailing stop tracker
        self.earth_agent.update_unrealized_pnl(symbol, position_pnl_pct)
        
        # V17: Check 60-day hard limit
        days_held = self.earth_agent.get_days_held(symbol, current_date)
        if days_held >= self.earth_agent.MAX_HOLD_DAYS:
            return True, "time_based"
        
        # V17: Check trailing stop
        if self.earth_agent.check_trailing_stop(symbol, position_pnl_pct):
            return True, "trailing_profit_stop"
        
        # Update peak for Fire agent
        if symbol in self.fire_agent.peak_prices:
            if current_price > self.fire_agent.peak_prices[symbol]:
                self.fire_agent.peak_prices[symbol] = current_price
        
        peak_price = self.fire_agent.peak_prices.get(symbol, entry_price)
        drawdown_from_peak = (peak_price - current_price) / peak_price if peak_price > 0 else 0
        
        # Water regime check (preserved)
        prices = list(self.fire_agent.price_history.get(symbol, []))
        if len(prices) >= 20:
            macro_signal = self.water_agent.get_macro_signal(prices)
            entry_risk_on = self.water_agent.entry_macro_score.get(symbol, 0.5)
            
            if symbol in BOND_SYMBOLS:
                if macro_signal.risk_on_score > entry_risk_on + 0.20:
                    return True, "water_bond_regime_shift"
        
        # Earth stop-loss
        if drawdown_from_peak > 0.15 and position_pnl_pct < 0:
            return True, f"earth_stop_{drawdown_from_peak:.1%}"
        
        # Fire volatility exit
        if len(prices) >= 20:
            returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                      for i in range(1, len(prices))]
            vol = statistics.stdev(returns) if len(returns) > 1 else 0.02
            
            if vol > 0.04 and position_pnl_pct < -0.05:
                return True, f"fire_vol_exit_{vol:.2f}"
        
        return False, ""
    
    def _get_dominant_planet(self, cycle_date: datetime) -> str:
        """Get dominant planet for the day"""
        planets = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]
        return planets[cycle_date.day % 7]
    
    def is_symbol_available(self, symbol: str, cycle_date) -> bool:
        """Check if symbol was listed on cycle_date"""
        if symbol in IPO_DATES:
            ipo_date = datetime.strptime(IPO_DATES[symbol], "%Y-%m-%d")
            if hasattr(cycle_date, 'date'):
                cycle_date = cycle_date.date()
            if hasattr(ipo_date, 'date'):
                ipo_date = ipo_date.date()
            return cycle_date >= ipo_date
        return True
    
    def record_trade_outcome(self, symbol: str, pnl: float, win: bool):
        """Record trade outcome for feedback"""
        self.earth_agent.record_exit(symbol, pnl, win)
        self.fire_agent.record_exit(symbol, pnl)
        self.water_agent.record_exit(symbol)
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        stats = {
            "consensus_achieved_pct": (self.consensus_count / self.total_cycles * 100) if self.total_cycles > 0 else 0,
            "execute_rate_pct": (self.execute_count / self.total_cycles * 100) if self.total_cycles > 0 else 0,
            "total_cycles": self.total_cycles,
            "consensus_count": self.consensus_count,
            "execute_count": self.execute_count,
            "vedastro_entries": self.vedastro_entries,
            "position_review_exits": self.position_review_exits,
        }
        
        return stats
