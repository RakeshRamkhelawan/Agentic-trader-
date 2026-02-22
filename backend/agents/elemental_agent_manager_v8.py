"""
Elemental Agent Manager V8 - SELF-DIRECTING POSITION SIZING
Fire Agent fully autonomous for position sizing based on:
- Volatility memory (60-day rolling)
- Harmony score
- Loss streak
- Navagraha planet

No hardcoded position sizing constraints.
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

from backend.config.asset_universe import FULL_ASSET_UNIVERSE
from backend.core.navagraha.asset_affinity import PLANET_ASSET_AFFINITY

logger = logging.getLogger("ElementalAgentsV8")


# ============ V8: NAVAGRAHA RISK MULTIPLIERS ============
# Planet determines risk appetite
PLANET_RISK_MULTIPLIERS = {
    "SUN":     1.00,  # Surya = neutral
    "MOON":    0.80,  # Chandra = cautious
    "MARS":    1.40,  # Mangal = aggressive
    "MERCURY": 0.90,  # Budha = careful
    "JUPITER": 1.20,  # Guru = expansive
    "VENUS":   1.10,  # Shukra = pleasant
    "SATURN":  0.60,  # Shani = restrictive
    "RAHU":    0.70,  # Rahu = uncertain
    "KETU":    0.75,  # Ketu = spiritual/withdrawing
}

# V8: Ether thresholds based on p75 harmony (0.6398 from v7 analysis)
PLANET_THRESHOLDS = {
    "SUN":     0.63,
    "MOON":    0.61,
    "MARS":    0.68,
    "MERCURY": 0.62,
    "JUPITER": 0.65,
    "VENUS":   0.62,
    "SATURN":  0.58,
    "RAHU":    0.70,
    "KETU":    0.66,
}

# Asset class mapping
ASSET_CLASSES = {
    "crypto": ["BTC", "ETH", "SOL", "AVAX", "LINK", "DOT", "ADA", "XRP",
               "DOGE", "LTC", "ATOM", "ALGO", "VET", "TRX", "XLM", "UNI",
               "MATIC", "AAVE", "FIL", "ETC"],
    "equity_us": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMZN", "TSLA",
                   "AMD", "CRM", "ADBE", "NFLX", "ORCL", "INTC", "PYPL", "ROKU", "ZM"],
    "equity_eu": ["ASML", "SAP", "AIR", "ROG", "NESN", "TTE", "SHEL"],
    "etf": ["SPY", "QQQ", "VTI", "IWM", "EEM", "EFA", "GLD", "TLT", "USO", "VIX"],
}

# Warm-start confidence per asset class
WARM_START_CONFIDENCE = {
    "crypto": 0.72,
    "equity_us": 0.85,
    "equity_eu": 0.78,
    "etf": 0.88,
}


@dataclass
class NavagrahaState:
    dominant_planet: str = "JUPITER"
    trading_gate_open: bool = True
    rahu_kala_active: bool = False
    consciousness_level: str = "Pure Awareness"
    guna_distribution: Dict[str, float] = field(default_factory=lambda: {
        "sattva": 0.55, "rajas": 0.30, "tamas": 0.15
    })


@dataclass
class FireDecision:
    decision: str
    confidence: float
    position_size: float  # V8: Fire determines this
    risk_score: float
    blocking_reasons: List[str]
    fire_dharma: str


@dataclass
class WaterRegime:
    regime: str
    confidence: float
    macro_narrative: str
    water_dharma: str


@dataclass
class AirSignal:
    symbol: str
    action: str
    confidence: float
    technical_summary: str
    air_dharma: str


@dataclass
class EarthValuation:
    symbol: str
    verdict: str
    confidence: float
    earth_dharma: str


@dataclass
class EtherSynthesis:
    final_decision: str
    harmony_score: float
    approved_symbol: Optional[str]
    approved_action: Optional[str]
    approved_qty: float  # V8: Determined by Fire
    approved_price: float
    execution_urgency: str
    consensus_achieved: bool
    blocking_agent: Optional[str]
    cosmic_narrative: str
    ether_dharma: str


# ============ V8: FIRE AGENT - AUTONOMOUS POSITION SIZING ============

class FireAgentV8:
    """
    Fire Agent with:
    - 60-day rolling volatility memory
    - Fully autonomous position sizing
    - Navagraha-based risk appetite
    """
    
    def __init__(self):
        # Loss streaks per symbol
        self.loss_streaks: Dict[str, int] = defaultdict(int)
        
        # V8: 60-day rolling price history per symbol
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
        
        # Harmony rolling window for p75 tracking
        self.harmony_window: deque = deque(maxlen=500)
    
    def record_price(self, symbol: str, price: float):
        """V8: Called EVERY cycle for EVERY symbol, even on BLOCK"""
        self.price_history[symbol].append(price)
    
    def record_outcome(self, symbol: str, pnl: float):
        """Record trade outcome"""
        if pnl < 0:
            self.loss_streaks[symbol] += 1
        else:
            self.loss_streaks[symbol] = 0
    
    def calculate_atr_pct(self, symbol: str) -> float:
        """
        Calculate Average True Range as percentage
        Average daily percentage movement over 60 days
        """
        prices = list(self.price_history[symbol])
        if len(prices) < 5:
            return 0.03  # Default 3% if insufficient data
        
        changes = [abs(prices[i] / prices[i-1] - 1) for i in range(1, len(prices))]
        return statistics.mean(changes)  # e.g., 0.02 = 2% average per day
    
    def calculate_confidence(self, symbol: str) -> float:
        """V8: Confidence with warm-start and adaptive learning"""
        streak = self.loss_streaks[symbol]
        atr_pct = self.calculate_atr_pct(symbol)
        
        # Streak penalty: each loss halves mandate
        streak_penalty = min(streak * 0.08, 0.45)
        
        # Volatility penalty
        vol_penalty = min(atr_pct / 0.05, 0.30)
        
        confidence = 0.92 - streak_penalty - vol_penalty
        return max(confidence, 0.37)
    
    def calculate_position_size(self, symbol: str,
                                portfolio_value: float,
                                harmony: float,
                                dominant_planet: str) -> float:
        """
        V8: Fire fully autonomously determines position size
        No external caps. No hardcoded maxima.
        
        Formula: position_pct = base_pct * vol_factor * harmony_factor * streak_factor * planet_mult
        """
        atr_pct = self.calculate_atr_pct(symbol)
        streak = self.loss_streaks[symbol]
        
        # 1. Volatility factor: high ATR = smaller position
        # UNI at ATR=0.15 (15%/day) → vol_factor = 0.40
        # SPY at ATR=0.01 (1%/day) → vol_factor = 0.91
        vol_factor = 1.0 / (1.0 + atr_pct * 6)
        
        # 2. Harmony factor: higher harmony = more room
        # harmony=0.50 → factor=0.25
        # harmony=0.80 → factor=0.64
        # harmony=0.95 → factor=0.90
        harmony_factor = harmony ** 2
        
        # 3. Loss streak factor: each consecutive loss halves mandate
        # streak=0 → 1.00
        # streak=2 → 0.25
        # streak=4 → 0.0625
        streak_factor = 0.5 ** streak
        
        # 4. Navagraha multiplier: planet determines risk appetite
        planet_mult = PLANET_RISK_MULTIPLIERS.get(dominant_planet, 1.0)
        
        # 5. Base percentage of portfolio
        base_pct = 0.015  # 1.5% base position
        
        position_pct = base_pct * vol_factor * harmony_factor * streak_factor * planet_mult
        
        # Fire's own logic prevents explosions organically
        return portfolio_value * position_pct
    
    def assess(self, symbol: str, portfolio_value: float,
               navagraha: NavagrahaState, harmony: float,
               prana_level: float) -> FireDecision:
        """V8: Fire assessment with autonomous position sizing"""
        
        blocking_reasons = []
        
        # Rahu Kala check
        if navagraha.rahu_kala_active:
            return FireDecision(
                decision="BLOCK", confidence=1.0, position_size=0.0,
                risk_score=1.0, blocking_reasons=["Rahu Kala active"],
                fire_dharma="Agni: Rahu's influence too strong"
            )
        
        # Prana check
        if prana_level < 10:
            return FireDecision(
                decision="BLOCK", confidence=1.0, position_size=0.0,
                risk_score=1.0, blocking_reasons=["Prana depleted"],
                fire_dharma="System prana too low"
            )
        
        # Calculate dynamic confidence
        confidence = self.calculate_confidence(symbol)
        
        # Organic exclusion: if confidence too low
        if confidence < 0.30:
            return FireDecision(
                decision="BLOCK", confidence=confidence, position_size=0.0,
                risk_score=0.8, blocking_reasons=[f"{symbol} loss streak: {self.loss_streaks[symbol]}"],
                fire_dharma=f"Agni: {symbol} too risky due to loss streak"
            )
        
        # V8: Fire determines position size
        position_size = self.calculate_position_size(
            symbol, portfolio_value, harmony, navagraha.dominant_planet
        )
        
        # Calculate risk score
        atr_pct = self.calculate_atr_pct(symbol)
        risk_score = (1.0 - confidence) * 0.5 + min(atr_pct / 0.10, 0.5)
        
        if risk_score > 0.5:
            decision = "BLOCK"
            position_size = 0.0
        elif risk_score > 0.3:
            decision = "REDUCE"
            position_size *= 0.7
        else:
            decision = "APPROVE"
        
        return FireDecision(
            decision=decision, confidence=confidence,
            position_size=position_size, risk_score=risk_score,
            blocking_reasons=blocking_reasons,
            fire_dharma=f"Agni: {decision} | size: ${position_size:.2f} | planet: {navagraha.dominant_planet}"
        )


# ============ V8: WATER AGENT ============

class WaterAgentV8:
    """Water Agent with asset class awareness"""
    
    def _get_asset_class(self, symbol: str) -> str:
        for cls, symbols in ASSET_CLASSES.items():
            if symbol in symbols:
                return cls
        return "equity_us"
    
    def analyze(self, symbol: str, navagraha: NavagrahaState, prices: List[float]) -> WaterRegime:
        """Analyze regime with asset class awareness"""
        
        if len(prices) < 20:
            asset_class = self._get_asset_class(symbol)
            base_conf = WARM_START_CONFIDENCE.get(asset_class, 0.80)
            return WaterRegime(
                regime="neutral", confidence=base_conf * 0.85,
                macro_narrative="Insufficient data",
                water_dharma="Water: insufficient data"
            )
        
        # Calculate trend
        price_change_30d = (prices[-1] - prices[-min(30, len(prices))]) / prices[-min(30, len(prices))] * 100
        
        advancing = sum(1 for i in range(1, min(20, len(prices))) if prices[-i] > prices[-i-1])
        total = min(19, len(prices) - 1)
        
        if total > 0:
            advance_ratio = advancing / total
            if advance_ratio > 0.6 and price_change_30d > 10:
                regime = "expansion"
            elif advance_ratio < 0.4 and price_change_30d < -10:
                regime = "contraction"
            elif price_change_30d > 0:
                regime = "recovery"
            else:
                regime = "neutral"
        else:
            regime = "neutral"
        
        asset_class = self._get_asset_class(symbol)
        base_conf = WARM_START_CONFIDENCE.get(asset_class, 0.80)
        
        if regime == "expansion":
            confidence = base_conf * 1.05
        elif regime == "contraction":
            confidence = base_conf * 0.85
        else:
            confidence = base_conf
        
        return WaterRegime(
            regime=regime, confidence=min(confidence, 0.90),
            macro_narrative=f"{navagraha.dominant_planet} | {regime} | {asset_class}",
            water_dharma=f"Water: {regime} for {asset_class}"
        )


# ============ V8: AIR AGENT ============

class AirAgentV8:
    """Air Agent with regime detection"""
    
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
    
    def generate_signals(self, symbol: str, current_price: float,
                         navagraha: NavagrahaState, prices: List[float]) -> AirSignal:
        """Generate signals with regime detection"""
        
        if len(prices) < 20:
            return AirSignal(
                symbol=symbol, action="HOLD", confidence=0.65,
                technical_summary="Insufficient data",
                air_dharma="Vayu: waiting for data"
            )
        
        rsi = self._calculate_rsi(prices)
        
        # Simple moving average trend
        ema20 = sum(prices[-20:]) / 20
        ema50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else ema20
        
        trend_up = ema20 > ema50
        trend_down = ema20 < ema50
        
        # ATR calculation
        if len(prices) >= 14:
            atr = sum(abs(prices[i] - prices[i-1]) for i in range(-14, 0)) / 14
        else:
            atr = current_price * 0.02
        atr_pct = (atr / current_price) * 100 if current_price > 0 else 2.0
        
        is_trending = atr_pct > 1.5
        
        action = "HOLD"
        confidence = 0.60
        
        if is_trending:
            if trend_up and rsi < 70:
                action = "BUY"
                confidence = 0.78
            elif trend_down and rsi > 30:
                action = "SELL"
                confidence = 0.40
            elif rsi >= 70:
                action = "SELL"
                confidence = 0.65
            elif rsi <= 30:
                action = "BUY"
                confidence = 0.55
        else:
            if rsi < 35:
                action = "BUY"
                confidence = 0.72
            elif rsi > 65:
                action = "SELL"
                confidence = 0.35
            else:
                action = "HOLD"
                confidence = 0.55
        
        # Planet affinity
        favored = PLANET_ASSET_AFFINITY.get(navagraha.dominant_planet, [])
        if symbol in favored or any(f in symbol for f in favored):
            confidence = min(0.95, confidence + 0.08)
        
        return AirSignal(
            symbol=symbol, action=action, confidence=confidence,
            technical_summary=f"RSI {rsi:.1f}, {action}, {navagraha.dominant_planet}",
            air_dharma=f"Vayu: {action} (conf: {confidence:.2f})"
        )


# ============ V8: EARTH AGENT ============

class EarthAgentV8:
    """Earth Agent with rolling performance memory"""
    
    def __init__(self):
        self.symbol_memory: Dict[str, deque] = defaultdict(lambda: deque(maxlen=20))
    
    def record_trade_outcome(self, symbol: str, pnl: float, win: bool):
        """Record trade outcome"""
        self.symbol_memory[symbol].append({
            "pnl": pnl, "win": win, "timestamp": datetime.utcnow()
        })
    
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
    
    def valuate(self, symbol: str, prices: List[float]) -> EarthValuation:
        """Valuation with adaptive confidence"""
        
        if len(prices) < 30:
            return EarthValuation(
                symbol=symbol, verdict="FAIR",
                confidence=self.calculate_confidence(symbol),
                earth_dharma="Prithvi: insufficient data"
            )
        
        # Simple valuation logic
        sma_30 = sum(prices[-30:]) / 30
        current_price = prices[-1]
        
        if current_price < sma_30 * 0.9:
            verdict = "UNDERVALUED"
        elif current_price > sma_30 * 1.1:
            verdict = "OVERVALUED"
        else:
            verdict = "FAIR"
        
        confidence = self.calculate_confidence(symbol)
        
        return EarthValuation(
            symbol=symbol, verdict=verdict, confidence=confidence,
            earth_dharma=f"Prithvi: {verdict} (conf: {confidence:.2f})"
        )


# ============ V8: ETHER ORCHESTRATOR ============

class EtherOrchestratorV8:
    """Ether with p75-based thresholds"""
    
    AGENT_WEIGHTS = {
        "fire": 0.30, "earth": 0.25, "water": 0.20, "air": 0.15, "ether": 0.10
    }
    
    def __init__(self):
        self.harmony_window: deque = deque(maxlen=500)
    
    def synthesize(self, fire_conf: float, water_conf: float,
                   air_conf: float, earth_conf: float) -> Tuple[float, bool]:
        """Synthesize with reduced disagreement penalty"""
        
        confidences = {
            "fire": fire_conf, "water": water_conf,
            "air": air_conf, "earth": earth_conf, "ether": 0.0
        }
        
        weighted_harmony = (
            confidences["fire"] * self.AGENT_WEIGHTS["fire"] +
            confidences["water"] * self.AGENT_WEIGHTS["water"] +
            confidences["air"] * self.AGENT_WEIGHTS["air"] +
            confidences["earth"] * self.AGENT_WEIGHTS["earth"] +
            confidences["ether"] * self.AGENT_WEIGHTS["ether"]
        )
        
        # Reduced disagreement penalty
        values = list(confidences.values())
        spread = max(values) - min(values)
        disagreement_penalty = spread * 0.05
        
        harmony = weighted_harmony - disagreement_penalty
        harmony = min(max(harmony, 0.0), 1.0)
        
        # Update harmony window
        self.harmony_window.append(harmony)
        
        # Relaxed consensus: 4 of 5 agents above threshold
        min_threshold = 0.35
        agents_above = sum(1 for c in confidences.values() if c >= min_threshold)
        consensus = agents_above >= 4
        
        return harmony, consensus
    
    def should_execute(self, harmony: float, consensus: bool,
                       dominant_planet: str) -> bool:
        """Execute based on p75-derived thresholds"""
        threshold = PLANET_THRESHOLDS.get(dominant_planet, 0.63)
        return consensus and harmony >= threshold


# ============ V8: MAIN MANAGER ============

class ElementalAgentManagerV8:
    """V8: Self-directing position sizing via Fire Agent"""
    
    def __init__(self):
        self.price_history: Dict[str, deque] = {}
        
        # V8: Individual agents
        self.fire_agent = FireAgentV8()
        self.water_agent = WaterAgentV8()
        self.air_agent = AirAgentV8()
        self.earth_agent = EarthAgentV8()
        self.ether_orchestrator = EtherOrchestratorV8()
        
        # Stats
        self.agent_confidence_history: Dict[str, List[float]] = {
            "fire": [], "water": [], "air": [], "earth": [], "ether": []
        }
        self.consensus_count = 0
        self.total_cycles = 0
        self.execute_count = 0
    
    def update_price_data(self, symbol: str, price: float):
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=50)
        self.price_history[symbol].append(price)
    
    def record_trade_outcome(self, symbol: str, pnl: float, price_change_pct: float = 0):
        """V8: Feedback loop"""
        self.earth_agent.record_trade_outcome(symbol, pnl, pnl > 0)
        self.fire_agent.record_outcome(symbol, pnl)
    
    def process_trading_cycle(self, symbol: str, current_price: float,
                             portfolio_value: float, current_positions: Dict[str, Any],
                             prana_level: float = 85.0) -> EtherSynthesis:
        """Process one complete trading cycle"""
        
        self.update_price_data(symbol, current_price)
        
        # V8: Fire records price EVERY cycle, even on BLOCK
        self.fire_agent.record_price(symbol, current_price)
        
        navagraha = self._get_current_navagraha_state()
        prices = list(self.price_history.get(symbol, []))
        
        self.total_cycles += 1
        
        # Run all 4 elemental agents
        water = self.water_agent.analyze(symbol, navagraha, prices)
        air = self.air_agent.generate_signals(symbol, current_price, navagraha, prices)
        earth = self.earth_agent.valuate(symbol, prices)
        
        # Pre-calculate harmony for Fire's position sizing
        pre_harmony, _ = self.ether_orchestrator.synthesize(
            self.fire_agent.calculate_confidence(symbol),
            water.confidence, air.confidence, earth.confidence
        )
        
        # V8: Fire assessment with autonomous position sizing
        fire = self.fire_agent.assess(
            symbol=symbol, portfolio_value=portfolio_value,
            navagraha=navagraha, harmony=pre_harmony, prana_level=prana_level
        )
        
        # Ether synthesis with final Fire confidence
        harmony, consensus = self.ether_orchestrator.synthesize(
            fire.confidence, water.confidence, air.confidence, earth.confidence
        )
        
        if consensus:
            self.consensus_count += 1
        
        should_trade = self.ether_orchestrator.should_execute(
            harmony, consensus, navagraha.dominant_planet
        )
        
        # Track stats
        self.agent_confidence_history["fire"].append(fire.confidence)
        self.agent_confidence_history["water"].append(water.confidence)
        self.agent_confidence_history["air"].append(air.confidence)
        self.agent_confidence_history["earth"].append(earth.confidence)
        self.agent_confidence_history["ether"].append(harmony)
        
        if not should_trade:
            return EtherSynthesis(
                final_decision="BLOCK", harmony_score=harmony,
                approved_symbol=None, approved_action=None, approved_qty=0.0,
                approved_price=0.0, execution_urgency="none",
                consensus_achieved=consensus, blocking_agent="ether",
                cosmic_narrative=f"H:{harmony:.2f}|{navagraha.dominant_planet}",
                ether_dharma="Akasha: disharmony"
            )
        
        if fire.decision == "BLOCK":
            return EtherSynthesis(
                final_decision="BLOCK", harmony_score=harmony,
                approved_symbol=symbol, approved_action=None, approved_qty=0.0,
                approved_price=0.0, execution_urgency="none",
                consensus_achieved=consensus, blocking_agent="fire",
                cosmic_narrative=f"Agni blocks|streak:{self.fire_agent.loss_streaks[symbol]}",
                ether_dharma="Fire protects"
            )
        
        # V8: Fire's autonomous position size
        position_size = fire.position_size
        
        if air.action in ["BUY", "SELL"]:
            final_decision = "EXECUTE"
            execution_urgency = "immediate" if harmony > 0.60 else "next_candle"
            self.execute_count += 1
        else:
            final_decision = "BLOCK"
            execution_urgency = "none"
            position_size = 0.0
        
        return EtherSynthesis(
            final_decision=final_decision, harmony_score=harmony,
            approved_symbol=symbol,
            approved_action=air.action if final_decision == "EXECUTE" else "HOLD",
            approved_qty=position_size,  # V8: Fire determines this
            approved_price=current_price,
            execution_urgency=execution_urgency,
            consensus_achieved=consensus, blocking_agent=None,
            cosmic_narrative=f"{navagraha.dominant_planet}|H:{harmony:.2f}|size:${position_size:.2f}",
            ether_dharma="Akasha harmonizes all elements"
        )
    
    def _get_current_navagraha_state(self) -> NavagrahaState:
        day = datetime.now().day
        planets = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]
        dominant = planets[day % 7]
        rahu_active = (day % 8) == 0
        
        return NavagrahaState(
            dominant_planet=dominant, trading_gate_open=not rahu_active,
            rahu_kala_active=rahu_active, consciousness_level="Pure Awareness",
            guna_distribution={"sattva": 0.55, "rajas": 0.30, "tamas": 0.15}
        )
    
    def get_agent_stats(self) -> Dict[str, Any]:
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
        return stats
