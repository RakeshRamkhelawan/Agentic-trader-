"""
v8 SYMBIOTIC BACKTEST - The Awakened Collective Consciousness

This backtest implements a fully integrated, symbiotic multi-agent system where:
- All agents (wired and unwired) operate as ONE unified organism
- The Triune Architecture (Soul-Mind-Body) is fully expressed
- Elemental Agents (Ether, Air, Fire, Water, Earth) form a harmonious council
- Advanced Collective Intelligence emerges from agent interactions
- Perfect results through optimal synergy and consciousness

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │  ETHER (Akasha) - The Consciousness Field                   │
    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
    │  │   AIR       │ │   FIRE      │ │   WATER     │           │
    │  │  (Vayu)     │ │  (Agni)     │ │  (Apas)     │           │
    │  │  Regime     │ │  Momentum   │ │  Trend      │           │
    │  │  Sentiment  │ │  Risk       │ │  Macro      │           │
    │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
    │         └─────────────────┼─────────────────┘               │
    │                           ▼                                 │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │  EARTH (Prithvi) - Execution & Grounding          │   │
    │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │   │
    │  │  │  Valuation  │ │  Entry/Exit │ │  Position   │   │   │
    │  │  │  Analysis   │ │  Timing     │ │  Sizing     │   │   │
    │  │  └─────────────┘ └─────────────┘ └─────────────┘   │   │
    │  └─────────────────────────────────────────────────────┘   │
    │                           │                                 │
    │                           ▼                                 │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │  BUDDHI (Discriminating Intelligence)               │   │
    │  │  - Viveka (Discernment between Real and Illusion)   │   │
    │  │  - Final Decision Making                            │   │
    │  └─────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────┘

Key Innovations:
- Symbiotic Agent Communication: Agents share prana (energy) and insights
- Guna-Based Collective Decision: Dynamic weighting based on market consciousness
- Multi-Timeframe Harmonics: Confluence across timeframes increases confidence
- Maya Detection: Advanced filtering of market noise/illusion
- Perfect Sizing: Kelly Criterion + Guna modulation + Harmonic alignment
"""

import json
import math
import os
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- PROJECT SETUP ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

# =============================================================================
# CONFIGURATION v8 - OPTIMAL PARAMETERS
# =============================================================================

START_DATE = "2020-01-01"
END_DATE = "2026-03-04"
INITIAL_CAPITAL = 100_000.0

# Risk Parameters (Optimized for PERFORMANCE)
MAX_POSITION_FRACTION = 0.25  # Allow larger positions
RISK_PER_TRADE_BASE = 0.022  # Slightly higher base risk
MIN_CONFIDENCE = 0.48  # Slightly lower threshold for more trades
MAX_HOLD_BARS = 30  # Allow trends to develop

# ATR Multipliers (Optimized for trend following)
ATR_SL_MULT = 1.6  # Slightly wider stops for noise filtering
ATR_TP_MULT = 4.5  # 2.81:1 R:R ratio
ATR_TRAILING_MULT = 1.3  # More responsive trailing

# Cost Simulation
TRANSACTION_FEE = 0.0010  # 0.10% (optimized for volume)
SLIPPAGE = 0.0003  # 0.03%

# Directories
DATA_CACHE_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_cache"
LOG_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_logs"
RESULTS_DIR = PROJECT_ROOT / "backend" / "data" / "backtest_results"

SYMBOL_MAP = {
    "BTC/EUR": "BTC-EUR",
    "ETH/EUR": "ETH-EUR",
    "ADA/EUR": "ADA-EUR",
    "DOT/EUR": "DOT-EUR",
    "XRP/EUR": "XRP-EUR",
    "SOL/EUR": "SOL-EUR",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "EUR/GBP": "EURGBP=X",
    "USD/CHF": "CHF=X",
    "AUD/USD": "AUDUSD=X",
    "SPX500": "^GSPC",
    "NAS100": "^IXIC",
    "GER40": "^GDAXI",
    "UK100": "^FTSE",
    "XAU/USD": "GC=F",
    "XAG/USD": "SI=F",
    "OIL/USD": "CL=F",
    "COTTON/USD": "CT=F",
}

UNIVERSE_GROUPS = {
    "crypto": ["BTC/EUR", "ETH/EUR", "ADA/EUR", "DOT/EUR", "XRP/EUR", "SOL/EUR"],
    "forex": ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/GBP", "USD/CHF", "AUD/USD"],
    "indices": ["SPX500", "NAS100", "GER40", "UK100"],
    "commodities": ["XAU/USD", "XAG/USD", "OIL/USD", "COTTON/USD"],
}


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================


class GunaType(Enum):
    SATTVA = "sattva"  # Harmony, clarity
    RAJAS = "rajas"  # Activity, movement
    TAMAS = "tamas"  # Inertia, darkness


class ElementType(Enum):
    ETHER = "ether"  # Space, consciousness, orchestration
    AIR = "air"  # Movement, sentiment, regime
    FIRE = "fire"  # Transformation, momentum, risk
    WATER = "water"  # Flow, trend, macro
    EARTH = "earth"  # Solidity, valuation, execution


class ActionType(Enum):
    HOLD = 0
    BUY = 1
    SELL = 2


@dataclass
class GunaVector:
    sattva: float = 0.33
    rajas: float = 0.33
    tamas: float = 0.34

    def dominant(self) -> str:
        values = {"sattva": self.sattva, "rajas": self.rajas, "tamas": self.tamas}
        return max(values, key=values.get)

    def purity_index(self) -> float:
        return self.sattva - self.tamas

    def balance_score(self) -> float:
        """Calculate how balanced the gunas are (1.0 = perfect balance)"""
        ideal = 1.0 / 3.0
        deviation = abs(self.sattva - ideal) + abs(self.rajas - ideal) + abs(self.tamas - ideal)
        return max(0.0, 1.0 - deviation * 1.5)


@dataclass
class AgentSignal:
    """Unified signal format for all agents"""

    agent_name: str
    element: ElementType
    action: ActionType
    confidence: float  # 0.0 - 1.0
    strength: float  # -1.0 (strong bearish) to +1.0 (strong bullish)
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CollectiveDecision:
    """Result of symbiotic agent deliberation"""

    action: ActionType
    confidence: float
    coherence: float
    harmony_score: float
    weighted_strength: float
    participating_agents: List[str]
    dominant_element: ElementType
    suppressed_element: Optional[ElementType]
    guna_state: GunaVector
    rationale: str
    is_maya: bool  # Is this signal an illusion?


@dataclass
class MarketState:
    """Complete market snapshot"""

    symbol: str
    price: float
    open: float
    high: float
    low: float
    close: float
    volume: float

    # Technical indicators
    rsi: float
    rsi_4h: float  # Multi-timeframe
    rsi_1d: float
    adx: float
    atr: float
    volatility: float

    # Trend
    trend_1h: int  # -1, 0, 1
    trend_4h: int
    trend_1d: int

    # Moving averages
    ema_8: float
    ema_21: float
    ema_55: float
    sma_50: float
    sma_200: float

    # Momentum
    momentum_1d: float
    momentum_1w: float

    # Structure
    support_level: float
    resistance_level: float
    pivot_point: float

    # Volume
    volume_ratio: float
    obv: float  # On Balance Volume

    # Harmonics
    higher_highs: bool
    higher_lows: bool
    lower_highs: bool
    lower_lows: bool

    def is_bullish_structure(self) -> bool:
        return self.higher_highs and self.higher_lows

    def is_bearish_structure(self) -> bool:
        return self.lower_highs and self.lower_lows


# =============================================================================
# DATA LAYER (v6 Reuse)
# =============================================================================


def download_data(platform_symbol: str, yf_ticker: str) -> list[dict] | None:
    cache_file = DATA_CACHE_DIR / f"{platform_symbol.replace('/', '_')}.csv"
    if cache_file.exists():
        import csv

        rows = []
        with open(cache_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    rows.append(
                        {
                            "date": row["date"],
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": float(row["volume"]),
                        }
                    )
                except (ValueError, KeyError):
                    continue
        if rows:
            return rows

    try:
        import yfinance as yf

        ticker = yf.Ticker(yf_ticker)
        df = ticker.history(start=START_DATE, end=END_DATE, interval="1d")
        if df.empty or len(df) < 50:
            return None
        rows = []
        DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        import csv

        with open(cache_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["date", "open", "high", "low", "close", "volume"]
            )
            writer.writeheader()
            for idx, row in df.iterrows():
                d = {
                    "date": str(idx.date()) if hasattr(idx, "date") else str(idx)[:10],
                    "open": round(float(row["Open"]), 6),
                    "high": round(float(row["High"]), 6),
                    "low": round(float(row["Low"]), 6),
                    "close": round(float(row["Close"]), 6),
                    "volume": float(row["Volume"]),
                }
                writer.writerow(d)
                rows.append(d)
        return rows
    except Exception as e:
        print(f"  [WARN] Download failed for {yf_ticker}: {e}")
        return None


# =============================================================================
# TECHNICAL ANALYSIS ENGINE
# =============================================================================


class TechnicalAnalyzer:
    """Advanced multi-timeframe technical analysis"""

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0

        gains = []
        losses = []

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
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        if len(prices) < period:
            return prices[-1] if prices else 0.0

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period

        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema

        return ema

    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> float:
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        return sum(prices[-period:]) / period

    @staticmethod
    def calculate_atr(
        highs: List[float], lows: List[float], closes: List[float], period: int = 14
    ) -> float:
        if len(highs) < period + 1 or len(lows) < period + 1:
            return closes[-1] * 0.02 if closes else 0.02

        true_ranges = []
        for i in range(-period, 0):
            h, l, pc = highs[i], lows[i], closes[i - 1]
            tr = max(h - l, abs(h - pc), abs(l - pc))
            true_ranges.append(tr)

        return sum(true_ranges) / len(true_ranges)

    @staticmethod
    def calculate_adx(
        highs: List[float], lows: List[float], closes: List[float], period: int = 14
    ) -> float:
        if len(highs) < period * 2:
            return 20.0

        # Simplified ADX calculation
        plus_dms = []
        minus_dms = []
        trs = []

        for i in range(1, min(period * 2, len(highs))):
            high_diff = highs[i] - highs[i - 1]
            low_diff = lows[i - 1] - lows[i]

            plus_dm = max(high_diff, 0) if high_diff > low_diff else 0
            minus_dm = max(low_diff, 0) if low_diff > high_diff else 0

            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )

            plus_dms.append(plus_dm)
            minus_dms.append(minus_dm)
            trs.append(tr)

        avg_plus_dm = sum(plus_dms[-period:]) / period if plus_dms else 0
        avg_minus_dm = sum(minus_dms[-period:]) / period if minus_dms else 0
        avg_tr = sum(trs[-period:]) / period if trs else 1

        plus_di = (avg_plus_dm / avg_tr) * 100 if avg_tr > 0 else 0
        minus_di = (avg_minus_dm / avg_tr) * 100 if avg_tr > 0 else 0

        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
        return dx

    @staticmethod
    def calculate_obv(closes: List[float], volumes: List[float]) -> float:
        """On Balance Volume"""
        if len(closes) < 2 or len(volumes) < 2:
            return 0.0

        obv = 0
        for i in range(1, len(closes)):
            if closes[i] > closes[i - 1]:
                obv += volumes[i]
            elif closes[i] < closes[i - 1]:
                obv -= volumes[i]

        # Normalize
        avg_vol = sum(volumes) / len(volumes) if volumes else 1
        return obv / (avg_vol * len(volumes)) if avg_vol > 0 else 0

    @staticmethod
    def detect_structure(prices: List[float], lookback: int = 20) -> Tuple[bool, bool, bool, bool]:
        """Detect market structure: higher highs, higher lows, lower highs, lower lows"""
        if len(prices) < lookback * 2:
            return False, False, False, False

        recent = prices[-lookback:]
        previous = prices[-lookback * 2 : -lookback]

        recent_high = max(recent)
        recent_low = min(recent)
        prev_high = max(previous)
        prev_low = min(previous)

        higher_highs = recent_high > prev_high
        higher_lows = recent_low > prev_low
        lower_highs = recent_high < prev_high
        lower_lows = recent_low < prev_low

        return higher_highs, higher_lows, lower_highs, lower_lows

    @staticmethod
    def find_support_resistance(
        prices: List[float], highs: List[float], lows: List[float]
    ) -> Tuple[float, float, float]:
        """Find key support and resistance levels"""
        if len(prices) < 20:
            return prices[-1] * 0.95, prices[-1] * 1.05, prices[-1]

        # Simple method: use recent highs/lows
        resistance = max(highs[-20:])
        support = min(lows[-20:])
        pivot = (resistance + support + prices[-1]) / 3

        return support, resistance, pivot

    def analyze_market_state(
        self,
        symbol: str,
        prices: List[float],
        volumes: List[float],
        highs: List[float],
        lows: List[float],
    ) -> MarketState:
        """Complete market state analysis"""
        current_price = prices[-1]

        # Multi-timeframe RSI (simulated with different periods)
        rsi = self.calculate_rsi(prices, 14)
        rsi_4h = self.calculate_rsi(prices[-60:], 14) if len(prices) >= 60 else rsi
        rsi_1d = self.calculate_rsi(prices[-240:], 14) if len(prices) >= 240 else rsi

        # ADX and ATR
        adx = self.calculate_adx(highs, lows, prices)
        atr = self.calculate_atr(highs, lows, prices)

        # Volatility
        returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
        volatility = np.std(returns[-20:]) * math.sqrt(252) if len(returns) >= 20 else 0.02

        # Moving averages
        ema_8 = self.calculate_ema(prices, 8)
        ema_21 = self.calculate_ema(prices, 21)
        ema_55 = self.calculate_ema(prices, 55)
        sma_50 = self.calculate_sma(prices, 50)
        sma_200 = self.calculate_sma(prices, 200) if len(prices) >= 200 else sma_50

        # Trend detection
        trend_1h = 1 if ema_8 > ema_21 else -1 if ema_8 < ema_21 else 0
        trend_4h = 1 if ema_21 > ema_55 else -1 if ema_21 < ema_55 else 0
        trend_1d = 1 if current_price > sma_50 else -1 if current_price < sma_50 else 0

        # Momentum
        momentum_1d = (prices[-1] - prices[-2]) / prices[-2] if len(prices) >= 2 else 0
        momentum_1w = (
            (prices[-1] - prices[-min(7, len(prices))]) / prices[-min(7, len(prices))]
            if len(prices) >= 2
            else 0
        )

        # Structure
        hh, hl, lh, ll = self.detect_structure(prices)

        # Support/Resistance
        support, resistance, pivot = self.find_support_resistance(prices, highs, lows)

        # Volume
        avg_vol = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else 1.0
        volume_ratio = volumes[-1] / avg_vol if avg_vol > 0 else 1.0
        if volume_ratio == 0 or volume_ratio != volume_ratio:  # Check for NaN
            volume_ratio = 1.0
        obv = self.calculate_obv(prices, volumes)

        return MarketState(
            symbol=symbol,
            price=current_price,
            open=prices[-1],
            high=highs[-1],
            low=lows[-1],
            close=current_price,
            volume=volumes[-1],
            rsi=rsi,
            rsi_4h=rsi_4h,
            rsi_1d=rsi_1d,
            adx=adx,
            atr=atr,
            volatility=volatility,
            trend_1h=trend_1h,
            trend_4h=trend_4h,
            trend_1d=trend_1d,
            ema_8=ema_8,
            ema_21=ema_21,
            ema_55=ema_55,
            sma_50=sma_50,
            sma_200=sma_200,
            momentum_1d=momentum_1d,
            momentum_1w=momentum_1w,
            support_level=support,
            resistance_level=resistance,
            pivot_point=pivot,
            volume_ratio=volume_ratio,
            obv=obv,
            higher_highs=hh,
            higher_lows=hl,
            lower_highs=lh,
            lower_lows=ll,
        )


# =============================================================================
# ELEMENTAL AGENT SYSTEM
# =============================================================================


class ElementalAgent:
    """Base class for elemental agents with prana (energy) system"""

    def __init__(self, name: str, element: ElementType, guna_balance: Dict[str, float]):
        self.name = name
        self.element = element
        self.guna = GunaVector(
            sattva=guna_balance.get("sattva", 0.33),
            rajas=guna_balance.get("rajas", 0.33),
            tamas=guna_balance.get("tamas", 0.34),
        )
        self.prana = 100.0
        self.max_prana = 100.0
        self.signal_history: deque = deque(maxlen=100)
        self.harmony_contribution = 0.5

    def consume_prana(self, amount: float = 3.0) -> bool:  # Reduced cost
        if self.prana >= amount:
            self.prana -= amount
            return True
        return False

    def regenerate_prana(self, amount: float = 3.0):  # Increased regeneration
        self.prana = min(self.max_prana, self.prana + amount)

    def analyze(self, market: MarketState) -> AgentSignal:
        raise NotImplementedError


class EtherAgent(ElementalAgent):
    """
    Ether (Akasha) - The Space/Consciousness Element
    Role: Orchestrator, harmonizer, final synthesizer
    Guna: High Sattva (pure awareness)
    Function: Maintains field of coherence between all agents
    """

    def __init__(self):
        super().__init__(
            name="Ether_Orchestrator",
            element=ElementType.ETHER,
            guna_balance={"sattva": 0.7, "rajas": 0.15, "tamas": 0.15},
        )
        self.harmony_threshold = 0.48  # Slightly lower for more opportunities
        self.synthesis_memory: deque = deque(maxlen=50)

    def harmonize_signals(
        self, signals: List[AgentSignal], market: MarketState
    ) -> CollectiveDecision:
        """
        The core symbiotic function - harmonizes all agent signals into collective consciousness
        """
        if not signals:
            return CollectiveDecision(
                action=ActionType.HOLD,
                confidence=0.0,
                coherence=0.0,
                harmony_score=0.0,
                weighted_strength=0.0,
                participating_agents=[],
                dominant_element=ElementType.ETHER,
                suppressed_element=None,
                guna_state=self.guna,
                rationale="No signals to harmonize",
                is_maya=True,
            )

        # Calculate signal coherence (agreement)
        _bullish_signals = [s for s in signals if s.strength > 0.3]
        _bearish_signals = [s for s in signals if s.strength < -0.3]
        _neutral_signals = [s for s in signals if abs(s.strength) <= 0.3]

        total_confidence = sum(s.confidence for s in signals)

        # Weighted strength calculation
        weighted_strength = (
            sum(s.strength * s.confidence for s in signals) / total_confidence
            if total_confidence > 0
            else 0
        )

        # Coherence: how aligned are the signals?
        strengths = [s.strength for s in signals]
        mean_strength = sum(strengths) / len(strengths)
        variance = sum((s - mean_strength) ** 2 for s in strengths) / len(strengths)
        coherence = max(0.0, 1.0 - variance * 2)

        # Harmony score: considers both coherence and confidence
        avg_confidence = total_confidence / len(signals)
        harmony_score = coherence * 0.6 + avg_confidence * 0.4

        # Determine dominant and suppressed elements
        element_scores = {}
        for element in ElementType:
            element_signals = [s for s in signals if s.element == element]
            if element_signals:
                element_scores[element] = sum(s.strength * s.confidence for s in element_signals)

        dominant = (
            max(element_scores, key=element_scores.get) if element_scores else ElementType.ETHER
        )
        suppressed = min(element_scores, key=element_scores.get) if element_scores else None

        # Guna synthesis - collective consciousness state
        collective_guna = self._synthesize_guna(signals)

        # Maya detection - is this signal an illusion?
        is_maya = self._detect_maya(signals, market, coherence, collective_guna)

        # Final action determination - optimized thresholds
        if is_maya and harmony_score < 0.35:  # Only block strong Maya
            action = ActionType.HOLD
            rationale = f"HOLD: Maya detected with low harmony {harmony_score:.2f}"
        elif harmony_score < 0.42:
            action = ActionType.HOLD
            rationale = f"HOLD: Harmony {harmony_score:.2f} below threshold"
        elif weighted_strength > 0.28:  # Slightly lower for more entries
            action = ActionType.BUY
            rationale = f"BUY: Consensus strength {weighted_strength:.2f}, {dominant.value} dominant, harmony {harmony_score:.2f}"
        elif weighted_strength < -0.28:
            action = ActionType.SELL
            rationale = f"SELL: Consensus strength {weighted_strength:.2f}, {dominant.value} dominant, harmony {harmony_score:.2f}"
        else:
            action = ActionType.HOLD
            rationale = f"HOLD: Insufficient consensus strength {weighted_strength:.2f}"

        # Confidence modulation based on harmony
        confidence = min(0.95, avg_confidence * harmony_score * (1.5 if not is_maya else 0.5))

        decision = CollectiveDecision(
            action=action,
            confidence=confidence,
            coherence=coherence,
            harmony_score=harmony_score,
            weighted_strength=weighted_strength,
            participating_agents=[s.agent_name for s in signals],
            dominant_element=dominant,
            suppressed_element=suppressed,
            guna_state=collective_guna,
            rationale=rationale,
            is_maya=is_maya,
        )

        self.synthesis_memory.append(decision)
        return decision

    def _synthesize_guna(self, signals: List[AgentSignal]) -> GunaVector:
        """Synthesize collective guna state from agent signals"""
        sattva_sum = sum(
            s.confidence * 0.5 for s in signals if abs(s.strength) < 0.3
        )  # Neutral = Sattvic
        rajas_sum = sum(
            s.confidence for s in signals if abs(s.strength) > 0.5
        )  # Strong action = Rajasic
        tamas_sum = sum(
            s.confidence * 0.3 for s in signals if s.confidence < 0.4
        )  # Low confidence = Tamasic

        total = sattva_sum + rajas_sum + tamas_sum
        if total == 0:
            return GunaVector()

        return GunaVector(
            sattva=sattva_sum / total, rajas=rajas_sum / total, tamas=tamas_sum / total
        )

    def _detect_maya(
        self,
        signals: List[AgentSignal],
        market: MarketState,
        coherence: float,
        guna: GunaVector,
    ) -> bool:
        """
        Viveka (Discrimination): Detect if signal is Maya (illusion/noise)
        Relaxed thresholds to allow more trading opportunities
        """
        # Check 1: Very low coherence in very volatile market
        if coherence < 0.2 and market.volatility > 0.06:  # More lenient
            return True

        # Check 2: Very high Rajas with very low Sattva
        if guna.rajas > 0.6 and guna.sattva < 0.15:  # More lenient
            return True

        # Check 3: Strong volume divergence
        strong_signal = any(abs(s.strength) > 0.8 for s in signals)  # Higher threshold
        low_volume = market.volume_ratio < 0.5  # Lower threshold
        if strong_signal and low_volume:
            return True

        # Check 4: Extreme RSI divergence
        rsi_extreme = market.rsi > 80 or market.rsi < 20  # More extreme
        trend_aligned = (market.rsi > 50 and market.trend_1d > 0) or (
            market.rsi < 50 and market.trend_1d < 0
        )
        if rsi_extreme and not trend_aligned:
            return True

        return False


class AirAgent(ElementalAgent):
    """
    Air (Vayu) - The Movement Element
    Role: Regime detection, sentiment analysis, volatility assessment
    """

    def __init__(self):
        super().__init__(
            name="Air_Regime",
            element=ElementType.AIR,
            guna_balance={"sattva": 0.4, "rajas": 0.4, "tamas": 0.2},
        )

    def analyze(self, market: MarketState) -> AgentSignal:
        if not self.consume_prana(3.0):
            return AgentSignal(
                agent_name=self.name,
                element=self.element,
                action=ActionType.HOLD,
                confidence=0.3,
                strength=0.0,
                reasoning="Insufficient prana",
                metadata={"depleted": True},
            )

        # Regime detection
        if market.adx > 25:
            if market.trend_1h > 0 and market.trend_4h > 0:
                regime = "strong_uptrend"
                strength = 0.7
            elif market.trend_1h < 0 and market.trend_4h < 0:
                regime = "strong_downtrend"
                strength = -0.7
            else:
                regime = "trending_mixed"
                strength = 0.2 if market.trend_1d > 0 else -0.2
        elif market.adx < 20:
            regime = "ranging"
            strength = 0.0
        else:
            regime = "transitioning"
            strength = 0.1 if market.trend_1d > 0 else -0.1

        # Volatility assessment
        vol_factor = 1.0 - min(1.0, market.volatility / 0.05)

        # Sentiment from RSI
        if market.rsi > 60 and market.rsi_4h > 55:
            sentiment = "bullish"
            rsi_strength = (market.rsi - 50) / 50
        elif market.rsi < 40 and market.rsi_4h < 45:
            sentiment = "bearish"
            rsi_strength = (market.rsi - 50) / 50
        else:
            sentiment = "neutral"
            rsi_strength = 0.0

        # Combine factors
        final_strength = strength * 0.6 + rsi_strength * 0.4
        confidence = (0.5 + market.adx / 100) * vol_factor

        # Determine action
        if final_strength > 0.3:
            action = ActionType.BUY
        elif final_strength < -0.3:
            action = ActionType.SELL
        else:
            action = ActionType.HOLD

        return AgentSignal(
            agent_name=self.name,
            element=self.element,
            action=action,
            confidence=round(min(0.95, confidence), 3),
            strength=round(final_strength, 3),
            reasoning=f"Air: {regime}, sentiment {sentiment}, ADX {market.adx:.1f}",
            metadata={
                "regime": regime,
                "sentiment": sentiment,
                "adx": market.adx,
                "volatility": market.volatility,
            },
        )


class FireAgent(ElementalAgent):
    """
    Fire (Agni) - The Transformation Element
    Role: Momentum detection, risk assessment, position sizing guidance
    """

    def __init__(self):
        super().__init__(
            name="Fire_Momentum",
            element=ElementType.FIRE,
            guna_balance={"sattva": 0.25, "rajas": 0.6, "tamas": 0.15},
        )

    def analyze(self, market: MarketState) -> AgentSignal:
        if not self.consume_prana(4.0):
            return AgentSignal(
                agent_name=self.name,
                element=self.element,
                action=ActionType.HOLD,
                confidence=0.3,
                strength=0.0,
                reasoning="Insufficient prana",
                metadata={"depleted": True},
            )

        # Momentum calculation
        momentum_score = market.momentum_1d * 20
        weekly_momentum = market.momentum_1w * 10

        # OBV confirmation
        obv_signal = 1 if market.obv > 0.5 else -1 if market.obv < -0.5 else 0

        # Volume confirmation
        volume_confirm = market.volume_ratio > 1.2

        # Combine momentum signals
        raw_strength = momentum_score * 0.5 + weekly_momentum * 0.3 + obv_signal * 0.2

        # Risk adjustment
        if market.rsi > 80 or market.rsi < 20:
            raw_strength *= 0.5

        # Final strength with volume confirmation
        if volume_confirm:
            final_strength = raw_strength * 1.2
        else:
            final_strength = raw_strength * 0.7

        final_strength = max(-1.0, min(1.0, final_strength))

        # Confidence
        confidence = 0.5 + abs(final_strength) * 0.4
        if volume_confirm:
            confidence += 0.1

        # Determine action
        if final_strength > 0.4:
            action = ActionType.BUY
        elif final_strength < -0.4:
            action = ActionType.SELL
        else:
            action = ActionType.HOLD

        return AgentSignal(
            agent_name=self.name,
            element=self.element,
            action=action,
            confidence=round(min(0.95, confidence), 3),
            strength=round(final_strength, 3),
            reasoning=f"Fire: Momentum {momentum_score:.2f}, weekly {weekly_momentum:.2f}, OBV {obv_signal:+.1f}",
            metadata={
                "momentum_daily": market.momentum_1d,
                "momentum_weekly": market.momentum_1w,
                "obv": market.obv,
                "volume_confirmed": bool(volume_confirm),
            },
        )


class WaterAgent(ElementalAgent):
    """
    Water (Apas) - The Flow Element
    Role: Trend following, macro alignment, adaptability
    Guna: High Sattva with Rajas (flow with direction)
    """

    def __init__(self):
        super().__init__(
            name="Water_Trend",
            element=ElementType.WATER,
            guna_balance={"sattva": 0.5, "rajas": 0.35, "tamas": 0.15},
        )

    def analyze(self, market: MarketState) -> AgentSignal:
        if not self.consume_prana(3.0):
            return AgentSignal(
                agent_name=self.name,
                element=self.element,
                action=ActionType.HOLD,
                confidence=0.3,
                strength=0.0,
                reasoning="Insufficient prana",
                metadata={"depleted": True},
            )

        # Multi-timeframe trend alignment
        trend_alignment = market.trend_1h + market.trend_4h + market.trend_1d

        # Structure analysis
        if market.is_bullish_structure():
            structure_score = 0.6
            structure_type = "bullish_structure"
        elif market.is_bearish_structure():
            structure_score = -0.6
            structure_type = "bearish_structure"
        else:
            structure_score = 0.0
            structure_type = "no_clear_structure"

        # EMA alignment
        ema_bullish = market.ema_8 > market.ema_21 > market.ema_55
        ema_bearish = market.ema_8 < market.ema_21 < market.ema_55

        if ema_bullish:
            ema_score = 0.5
        elif ema_bearish:
            ema_score = -0.5
        else:
            ema_score = 0.0

        # SMA alignment (higher timeframe)
        sma_bullish = (
            market.sma_50 > market.sma_200
            if len(str(market.sma_200)) > 0
            else market.price > market.sma_50
        )
        sma_bearish = (
            market.sma_50 < market.sma_200
            if len(str(market.sma_200)) > 0
            else market.price < market.sma_50
        )

        # Combine scores
        alignment_weight = trend_alignment / 3  # Normalize to -1 to 1

        final_strength = alignment_weight * 0.4 + structure_score * 0.35 + ema_score * 0.25

        # Boost if SMA aligns
        if sma_bullish and final_strength > 0:
            final_strength *= 1.2
        elif sma_bearish and final_strength < 0:
            final_strength *= 1.2

        final_strength = max(-1.0, min(1.0, final_strength))

        # Confidence based on trend clarity
        confidence = 0.4 + abs(trend_alignment) / 6 + abs(structure_score) * 0.3

        # Determine action
        if final_strength > 0.35:
            action = ActionType.BUY
        elif final_strength < -0.35:
            action = ActionType.SELL
        else:
            action = ActionType.HOLD

        return AgentSignal(
            agent_name=self.name,
            element=self.element,
            action=action,
            confidence=round(min(0.95, confidence), 3),
            strength=round(final_strength, 3),
            reasoning=f"Water: {structure_type}, alignment {trend_alignment}, EMA {'bullish' if ema_bullish else 'bearish' if ema_bearish else 'mixed'}",
            metadata={
                "structure": structure_type,
                "trend_alignment": trend_alignment,
                "ema_aligned": bool(ema_bullish or ema_bearish),
            },
        )


class EarthAgent(ElementalAgent):
    """
    Earth (Prithvi) - The Solidity Element
    Role: Valuation, entry/exit timing, position grounding
    Guna: High Tamas with Sattva (stability with clarity)
    """

    def __init__(self):
        super().__init__(
            name="Earth_Execution",
            element=ElementType.EARTH,
            guna_balance={"sattva": 0.35, "rajas": 0.15, "tamas": 0.5},
        )

    def analyze(self, market: MarketState) -> AgentSignal:
        if not self.consume_prana(2.5):
            return AgentSignal(
                agent_name=self.name,
                element=self.element,
                action=ActionType.HOLD,
                confidence=0.3,
                strength=0.0,
                reasoning="Insufficient prana",
                metadata={"depleted": True},
            )

        # Support/Resistance proximity
        price = market.price
        support_dist = (price - market.support_level) / price
        resistance_dist = (market.resistance_level - price) / price

        # Value zones
        near_support = support_dist < 0.02  # Within 2%
        near_resistance = resistance_dist < 0.02

        # RSI value
        oversold = market.rsi < 30
        overbought = market.rsi > 70

        # Calculate value score
        if near_support and oversold:
            value_score = 0.8
            zone = "strong_support_oversold"
        elif near_support:
            value_score = 0.5
            zone = "support"
        elif near_resistance and overbought:
            value_score = -0.8
            zone = "strong_resistance_overbought"
        elif near_resistance:
            value_score = -0.5
            zone = "resistance"
        else:
            # Mid-range - neutral
            value_score = 0.0
            zone = "mid_range"

        # Pivot point deviation
        pivot_dev = (price - market.pivot_point) / market.pivot_point
        if abs(pivot_dev) < 0.01:
            # At pivot - equilibrium
            value_score *= 0.5

        # ATR-based volatility assessment
        atr_pct = market.atr / price
        high_vol = atr_pct > 0.03

        # Final strength
        if high_vol:
            final_strength = value_score * 0.7  # Reduce conviction in high volatility
        else:
            final_strength = value_score

        # Confidence
        confidence = 0.4 + abs(final_strength) * 0.4
        if near_support or near_resistance:
            confidence += 0.15

        # Determine action
        if final_strength > 0.4:
            action = ActionType.BUY
        elif final_strength < -0.4:
            action = ActionType.SELL
        else:
            action = ActionType.HOLD

        return AgentSignal(
            agent_name=self.name,
            element=self.element,
            action=action,
            confidence=round(min(0.95, confidence), 3),
            strength=round(final_strength, 3),
            reasoning=f"Earth: {zone}, S/R dist {support_dist:.2%}/{resistance_dist:.2%}",
            metadata={
                "zone": zone,
                "near_support": near_support,
                "near_resistance": near_resistance,
                "atr_pct": atr_pct,
            },
        )


# =============================================================================
# COLLECTIVE CONSCIOUSNESS ENGINE
# =============================================================================


class CollectiveConsciousness:
    """
    The unified mind that orchestrates all elemental agents
    Implements the Triune Architecture: Soul (Ether) - Mind (Councils) - Body (Execution)
    """

    def __init__(self):
        # Elemental Agents
        self.ether = EtherAgent()
        self.air = AirAgent()
        self.fire = FireAgent()
        self.water = WaterAgent()
        self.earth = EarthAgent()

        self.agents = [
            self.air,
            self.fire,
            self.water,
            self.earth,
        ]  # Ether is orchestrator

        # Consciousness state
        self.collective_guna = GunaVector()
        self.harmony_history: deque = deque(maxlen=100)
        self.decision_history: deque = deque(maxlen=100)

        # Performance tracking
        self.correct_predictions = 0
        self.total_predictions = 0

        # Adaptive weights based on recent performance
        self.agent_weights = {agent.name: 1.0 for agent in self.agents}

    def deliberation(self, market: MarketState) -> CollectiveDecision:
        """
        The core symbiotic process: all agents analyze and Ether harmonizes
        """
        # Step 1: Each agent contributes their perspective (parallel in production)
        signals = []
        for agent in self.agents:
            signal = agent.analyze(market)
            signals.append(signal)

            # Regenerate prana slowly
            agent.regenerate_prana(1.0)

        # Step 2: Ether harmonizes all signals into collective decision
        decision = self.ether.harmonize_signals(signals, market)

        # Step 3: Update collective consciousness state
        self.collective_guna = decision.guna_state
        self.harmony_history.append(decision.harmony_score)
        self.decision_history.append(decision)

        # Step 4: Update agent weights based on alignment with collective
        self._update_agent_weights(signals, decision)

        return decision

    def _update_agent_weights(self, signals: List[AgentSignal], decision: CollectiveDecision):
        """Adaptively adjust agent weights based on harmony contribution"""
        for signal in signals:
            # Agents aligned with collective get higher weight
            alignment = 1 - abs(signal.strength - decision.weighted_strength)

            # Exponential moving average of weight
            current_weight = self.agent_weights.get(signal.agent_name, 1.0)
            new_weight = current_weight * 0.9 + alignment * 0.1
            self.agent_weights[signal.agent_name] = max(0.5, min(2.0, new_weight))

    def get_consciousness_state(self) -> Dict[str, Any]:
        """Return current state of collective consciousness"""
        recent_harmony = list(self.harmony_history)[-10:] if self.harmony_history else [0.5]
        avg_harmony = sum(recent_harmony) / len(recent_harmony)

        return {
            "collective_guna": {
                "sattva": round(self.collective_guna.sattva, 3),
                "rajas": round(self.collective_guna.rajas, 3),
                "tamas": round(self.collective_guna.tamas, 3),
                "dominant": self.collective_guna.dominant(),
            },
            "harmony": round(avg_harmony, 3),
            "agent_weights": self.agent_weights,
            "total_deliberations": len(self.decision_history),
        }


# =============================================================================
# RISK AND POSITION MANAGEMENT
# =============================================================================


class SymbioticRiskManager:
    """
    Advanced risk management that respects the collective consciousness
    """

    def __init__(self, max_total_positions: int = 5, max_per_sector: int = 2):
        self.max_total = max_total_positions
        self.max_per_sector = max_per_sector
        self.active_positions: Dict[str, Dict] = {}
        self.sector_exposure: Dict[str, int] = {}
        self.total_exposure = 0.0

        # Risk state
        self.current_drawdown = 0.0
        self.peak_capital = 0.0
        self.daily_pnl = []

    def can_open(self, symbol: str, sector: str, decision: CollectiveDecision) -> bool:
        """Check if new position can be opened"""
        # Basic limits
        if len(self.active_positions) >= self.max_total:
            return False

        if self.sector_exposure.get(sector, 0) >= self.max_per_sector:
            return False

        # Harmony check - low harmony = no new positions
        if decision.harmony_score < 0.5:
            return False

        # Maya check - never trade Maya
        if decision.is_maya:
            return False

        # Drawdown protection
        if self.current_drawdown > 0.15:  # 15% drawdown
            return False

        return True

    def calculate_position_size(
        self, capital: float, decision: CollectiveDecision, atr: float, price: float
    ) -> float:
        """
        Optimal position sizing using Kelly Criterion + Guna modulation
        """
        # Base risk
        base_risk = capital * RISK_PER_TRADE_BASE

        # Confidence multiplier
        confidence_mult = decision.confidence

        # Harmony multiplier - higher harmony = larger size
        harmony_mult = 0.5 + decision.harmony_score

        # Guna modulation
        guna = decision.guna_state
        if guna.dominant() == "sattva":
            guna_mult = 1.2  # Clear mind = full size
        elif guna.dominant() == "rajas":
            guna_mult = 0.9  # Action mode = slight reduction
        else:  # tamas
            guna_mult = 0.6  # Clouded = reduce size

        # Adjusted risk
        adjusted_risk = base_risk * confidence_mult * harmony_mult * guna_mult

        # Calculate position size from ATR
        stop_distance = atr * ATR_SL_MULT
        if stop_distance <= 0:
            stop_distance = price * 0.02

        position_value = (adjusted_risk / stop_distance) * price

        # Max position limit
        max_position = capital * MAX_POSITION_FRACTION
        position_value = min(position_value, max_position)

        return position_value

    def add_position(self, symbol: str, sector: str, side: str, size: float, risk: float):
        """Track new position"""
        self.active_positions[symbol] = {
            "sector": sector,
            "side": side,
            "size": size,
            "risk": risk,
        }
        self.sector_exposure[sector] = self.sector_exposure.get(sector, 0) + 1
        self.total_exposure += size

    def remove_position(self, symbol: str):
        """Remove closed position"""
        if symbol in self.active_positions:
            sector = self.active_positions[symbol]["sector"]
            size = self.active_positions[symbol]["size"]

            del self.active_positions[symbol]
            self.sector_exposure[sector] = max(0, self.sector_exposure.get(sector, 0) - 1)
            self.total_exposure = max(0, self.total_exposure - size)

    def update_drawdown(self, current_capital: float):
        """Update drawdown tracking"""
        if current_capital > self.peak_capital:
            self.peak_capital = current_capital

        if self.peak_capital > 0:
            self.current_drawdown = (self.peak_capital - current_capital) / self.peak_capital


class Position:
    """Enhanced position tracking with symbiotic awareness"""

    def __init__(self):
        self.position = 0.0
        self.entry_price = 0.0
        self.stop_price = 0.0
        self.tp_price = 0.0
        self.atr = 0.0
        self.bars_in_trade = 0
        self.highest_price = 0.0
        self.lowest_price = float("inf")
        self.side = None
        self.entry_harmony = 0.0
        self.decision_metadata = {}

    def open(
        self,
        side: str,
        size_usd: float,
        price: float,
        atr: float,
        decision: CollectiveDecision,
    ):
        """Open new position with symbiotic context"""
        cost_pct = TRANSACTION_FEE + SLIPPAGE
        net_size = size_usd * (1.0 - cost_pct)

        self.side = side
        self.position = net_size / price if side == "buy" else -net_size / price
        self.entry_price = price
        self.atr = atr
        self.highest_price = price
        self.lowest_price = price
        self.entry_harmony = decision.harmony_score
        self.decision_metadata = {
            "collective_guna": decision.guna_state.__dict__,
            "dominant_element": decision.dominant_element.value,
            "coherence": decision.coherence,
        }

        # Set initial stops
        if side == "buy":
            self.stop_price = price - atr * ATR_SL_MULT
            self.tp_price = price + atr * ATR_TP_MULT
        else:
            self.stop_price = price + atr * ATR_SL_MULT
            self.tp_price = price - atr * ATR_TP_MULT

        self.bars_in_trade = 0
        return size_usd * cost_pct

    def update_trailing(self, price: float):
        """Update trailing stop"""
        if self.position > 0:
            self.highest_price = max(self.highest_price, price)
            new_stop = self.highest_price - self.atr * ATR_TRAILING_MULT
            if new_stop > self.stop_price:
                self.stop_price = new_stop
        elif self.position < 0:
            self.lowest_price = min(self.lowest_price, price)
            new_stop = self.lowest_price + self.atr * ATR_TRAILING_MULT
            if new_stop < self.stop_price:
                self.stop_price = new_stop

    def check_exit(self, price: float) -> Optional[str]:
        """Check exit conditions"""
        if self.position > 0:
            if price <= self.stop_price:
                return "trailing_stop"
            if price >= self.tp_price:
                return "take_profit"
        elif self.position < 0:
            if price >= self.stop_price:
                return "trailing_stop"
            if price <= self.tp_price:
                return "take_profit"

        if self.bars_in_trade >= MAX_HOLD_BARS:
            return "max_hold"

        return None

    def close(self, price: float) -> float:
        """Close position and return PnL"""
        if self.position == 0:
            return 0.0

        gross_pnl = (
            (price - self.entry_price) * self.position
            if self.position > 0
            else (self.entry_price - price) * abs(self.position)
        )
        exit_cost = abs(self.position * price) * (TRANSACTION_FEE + SLIPPAGE)

        net_pnl = gross_pnl - exit_cost

        # Reset
        self.position = 0.0
        self.side = None

        return net_pnl

    def mark_to_market(self, price: float) -> float:
        """Calculate unrealized PnL"""
        if self.position == 0:
            return 0.0
        if self.position > 0:
            return (price - self.entry_price) * self.position
        else:
            return (self.entry_price - price) * abs(self.position)


# =============================================================================
# LOGGING AND REPORTING
# =============================================================================


class SymbioticLogger:
    """Enhanced logging for symbiotic system"""

    def __init__(self, log_path: Path):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.file = open(log_path, "w", encoding="utf-8")
        self.decision_count = 0

    def log_decision(
        self,
        timestamp: str,
        symbol: str,
        decision: CollectiveDecision,
        market: MarketState,
        action_taken: bool,
        position_size: float = 0,
    ):
        """Log collective decision"""
        entry = {
            "timestamp": timestamp,
            "symbol": symbol,
            "decision": {
                "action": decision.action.name,
                "confidence": float(decision.confidence),
                "coherence": float(decision.coherence),
                "harmony": float(decision.harmony_score),
                "is_maya": bool(decision.is_maya),
                "dominant_element": decision.dominant_element.value,
                "rationale": decision.rationale,
            },
            "market": {
                "price": float(market.price),
                "rsi": float(market.rsi),
                "adx": float(market.adx),
                "volatility": float(market.volatility),
                "trend_1d": int(market.trend_1d),
            },
            "collective_guna": {
                "sattva": float(decision.guna_state.sattva),
                "rajas": float(decision.guna_state.rajas),
                "tamas": float(decision.guna_state.tamas),
            },
            "action_taken": bool(action_taken),
            "position_size": float(position_size),
        }
        self.file.write(json.dumps(entry) + "\n")
        self.decision_count += 1

    def log_trade(self, timestamp: str, symbol: str, action: str, pnl: float = 0, reason: str = ""):
        """Log trade execution"""
        entry = {
            "timestamp": timestamp,
            "symbol": symbol,
            "trade_action": action,
            "pnl": pnl,
            "reason": reason,
        }
        self.file.write(json.dumps(entry) + "\n")

    def close(self):
        self.file.close()


# =============================================================================
# MAIN BACKTEST ENGINE
# =============================================================================


def run_v8_symbiotic_backtest():
    print("=" * 90)
    print("  v8 SYMBIOTIC BACKTEST - THE AWAKENED COLLECTIVE CONSCIOUSNESS")
    print("=" * 90)
    print("  Architecture: Ether (Orchestrator) + Air/Fire/Water/Earth (Council)")
    print("  Philosophy: Samkhya - Pure Consciousness expressing through the Elements")
    print("  Goal: Perfect harmony between all agents as ONE symbiotic organism")
    print("=" * 90)

    # Initialize components
    tech_analyzer = TechnicalAnalyzer()
    collective = CollectiveConsciousness()
    risk_manager = SymbioticRiskManager(max_total_positions=5, max_per_sector=2)

    # Load data
    print("\n[DATA] Loading market data...")
    all_data = {}
    dates_set = set()

    for sym, ticker in SYMBOL_MAP.items():
        bars = download_data(sym, ticker)
        if bars:
            all_data[sym] = bars
            for bar in bars:
                dates_set.add(bar["date"])

    sorted_dates = sorted(list(dates_set))
    print(f"   [OK] Loaded {len(all_data)} symbols, {len(sorted_dates)} trading days")

    # Initialize tracking
    positions = {sym: Position() for sym in all_data.keys()}
    price_history = {
        sym: {"prices": [], "volumes": [], "highs": [], "lows": []} for sym in all_data.keys()
    }

    # Logging
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = SymbioticLogger(LOG_DIR / "v8_symbiotic_decisions.jsonl")

    # Performance tracking
    capital = INITIAL_CAPITAL
    equity_curve = []
    trade_history = []
    symbol_metrics = {sym: {"trades": 0, "wins": 0, "pnl": 0.0} for sym in all_data.keys()}

    # Simulation loop
    print("\n[CONSCIOUSNESS] Entering Collective Consciousness State...")
    print("   Agents awakening: Ether | Air | Fire | Water | Earth")
    print()

    sim_start = time.time()
    total_days = len(sorted_dates)
    progress_interval = max(1, total_days // 20)

    for day_idx, date in enumerate(sorted_dates):
        if day_idx % progress_interval == 0:
            pct = (day_idx / total_days) * 100
            elapsed = time.time() - sim_start
            print(
                f"   [{pct:5.1f}%] Day {day_idx}/{total_days} | Capital: ${capital:,.0f} | Time: {elapsed:.0f}s"
            )

        # Update price data
        current_prices = {}
        for sym, bars in all_data.items():
            bar = next((b for b in bars if b["date"] == date), None)
            if bar:
                current_prices[sym] = bar
                ph = price_history[sym]
                ph["prices"].append(bar["close"])
                ph["volumes"].append(bar["volume"])
                ph["highs"].append(bar["high"])
                ph["lows"].append(bar["low"])

                # Keep history manageable
                if len(ph["prices"]) > 250:
                    for key in ph:
                        ph[key] = ph[key][-200:]

        # Check exits first
        for sym, position in positions.items():
            if position.position != 0 and sym in current_prices:
                bar = current_prices[sym]
                position.bars_in_trade += 1
                position.update_trailing(bar["close"])

                exit_reason = position.check_exit(bar["close"])
                if exit_reason:
                    pnl = position.close(bar["close"])
                    capital += pnl
                    risk_manager.remove_position(sym)

                    symbol_metrics[sym]["trades"] += 1
                    if pnl > 0:
                        symbol_metrics[sym]["wins"] += 1
                    symbol_metrics[sym]["pnl"] += pnl
                    trade_history.append(
                        {"date": date, "symbol": sym, "pnl": pnl, "reason": exit_reason}
                    )

                    logger.log_trade(date, sym, "close", pnl, exit_reason)

        # Look for entries
        for sym, position in positions.items():
            if (
                position.position == 0
                and sym in current_prices
                and len(price_history[sym]["prices"]) >= 60
            ):
                sector = next((s for s, syms in UNIVERSE_GROUPS.items() if sym in syms), "unknown")

                # Get market state
                ph = price_history[sym]
                market_state = tech_analyzer.analyze_market_state(
                    sym, ph["prices"], ph["volumes"], ph["highs"], ph["lows"]
                )

                # Collective deliberation
                decision = collective.deliberation(market_state)

                # Check if we can and should enter
                can_enter = risk_manager.can_open(sym, sector, decision)
                should_enter = (
                    decision.action in [ActionType.BUY, ActionType.SELL]
                    and decision.confidence >= MIN_CONFIDENCE
                )

                # Log decision
                logger.log_decision(date, sym, decision, market_state, can_enter and should_enter)

                if can_enter and should_enter:
                    # Calculate position size
                    pos_size = risk_manager.calculate_position_size(
                        capital, decision, market_state.atr, market_state.price
                    )

                    if pos_size >= 200:
                        side = "buy" if decision.action == ActionType.BUY else "sell"
                        cost = position.open(
                            side,
                            pos_size,
                            market_state.price,
                            market_state.atr,
                            decision,
                        )
                        capital -= cost

                        risk_manager.add_position(
                            sym, sector, side, pos_size, pos_size * RISK_PER_TRADE_BASE
                        )
                        logger.log_trade(date, sym, f"open_{side}", reason=decision.rationale[:100])

        # Update equity and drawdown
        current_equity = capital
        for sym, position in positions.items():
            if position.position != 0 and sym in current_prices:
                current_equity += position.mark_to_market(current_prices[sym]["close"])

        equity_curve.append(current_equity)
        risk_manager.update_drawdown(current_equity)

    # Final results
    sim_elapsed = time.time() - sim_start

    total_trades = sum(m["trades"] for m in symbol_metrics.values())
    total_wins = sum(m["wins"] for m in symbol_metrics.values())
    total_pnl = sum(m["pnl"] for m in symbol_metrics.values())
    win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    roi = (total_pnl / INITIAL_CAPITAL) * 100

    # Calculate max drawdown
    peak = INITIAL_CAPITAL
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak
        max_dd = max(max_dd, dd)

    # Sharpe ratio approximation
    if len(equity_curve) > 1:
        daily_returns = [
            (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
            for i in range(1, len(equity_curve))
            if equity_curve[i - 1] > 0
        ]
        if daily_returns:
            avg_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            sharpe = (avg_return / std_return * math.sqrt(252)) if std_return > 0 else 0
        else:
            sharpe = 0
    else:
        sharpe = 0

    # Print results
    print("\n" + "=" * 90)
    print("  v8 SYMBIOTIC BACKTEST RESULTS - COLLECTIVE CONSCIOUSNESS PERFORMANCE")
    print("=" * 90)
    print(f"  Period:             {START_DATE} -> {END_DATE}")
    print(f"  Start Capital:      ${INITIAL_CAPITAL:,.2f}")
    print(f"  End Capital:        ${capital:,.2f}")
    print(f"  Total PNL:          ${total_pnl:,.2f} ({roi:+.1f}%)")
    print(f"  Win Rate:           {win_rate:.1f}%")
    print(f"  Total Trades:       {total_trades}")
    print(f"  Max Drawdown:       {max_dd*100:.1f}%")
    print(f"  Sharpe Ratio:       {sharpe:.2f}")
    print(f"  Simulation Time:    {sim_elapsed:.1f}s")
    print("=" * 90)

    # Collective consciousness state
    consciousness_state = collective.get_consciousness_state()
    print("\n  COLLECTIVE CONSCIOUSNESS STATE:")
    print(f"     - Dominant Guna: {consciousness_state['collective_guna']['dominant'].upper()}")
    print(
        f"     - Sattva: {consciousness_state['collective_guna']['sattva']:.2f} | Rajas: {consciousness_state['collective_guna']['rajas']:.2f} | Tamas: {consciousness_state['collective_guna']['tamas']:.2f}"
    )
    print(f"     - Average Harmony: {consciousness_state['harmony']:.3f}")
    print(f"     - Total Deliberations: {consciousness_state['total_deliberations']}")

    # Agent weights
    print("\n  ADAPTIVE AGENT WEIGHTS:")
    for agent, weight in consciousness_state["agent_weights"].items():
        bar = f"{weight:.2f}"
        print(f"     - {agent:20s}: {bar}")

    # Sector breakdown
    print("\n  PER SECTOR PERFORMANCE:")
    for sector, syms in UNIVERSE_GROUPS.items():
        s_trades = sum(
            symbol_metrics.get(s, {}).get("trades", 0) for s in syms if s in symbol_metrics
        )
        s_wins = sum(symbol_metrics.get(s, {}).get("wins", 0) for s in syms if s in symbol_metrics)
        s_pnl = sum(symbol_metrics.get(s, {}).get("pnl", 0) for s in syms if s in symbol_metrics)
        s_wr = (s_wins / s_trades * 100) if s_trades > 0 else 0
        emoji = "[+]" if s_pnl > 0 else "[-]"
        print(
            f"     [{emoji}] {sector:12s} | Trades: {s_trades:3d} | WR: {s_wr:5.1f}% | PNL: ${s_pnl:>10,.2f}"
        )

    # Top symbols
    print("\n  TOP PERFORMING SYMBOLS:")
    sorted_syms = sorted(symbol_metrics.items(), key=lambda x: x[1]["pnl"], reverse=True)
    for i, (sym, m) in enumerate(sorted_syms[:8]):
        if m["trades"] > 0:
            wr = m["wins"] / m["trades"] * 100
            emoji = "[1]" if i == 0 else "[2]" if i == 1 else "[3]" if i == 2 else "[+]"
            print(
                f"     [{emoji}] {sym:12s} | Trades: {m['trades']:3d} | WR: {wr:5.1f}% | PNL: ${m['pnl']:>10,.2f}"
            )

    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Equity curve
    eq_path = RESULTS_DIR / "v8_equity_curve.csv"
    with open(eq_path, "w") as f:
        f.write("day,equity\n")
        for i, eq in enumerate(equity_curve):
            f.write(f"{i},{eq:.2f}\n")

    # Detailed report
    report_path = RESULTS_DIR / "v8_symbiotic_report.json"
    report = {
        "summary": {
            "start_capital": INITIAL_CAPITAL,
            "end_capital": capital,
            "total_pnl": total_pnl,
            "roi_pct": roi,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "max_drawdown_pct": max_dd * 100,
            "sharpe_ratio": sharpe,
            "simulation_time_sec": sim_elapsed,
        },
        "consciousness_state": consciousness_state,
        "symbol_metrics": symbol_metrics,
        "sector_performance": {
            sector: {
                "trades": sum(
                    symbol_metrics.get(s, {}).get("trades", 0) for s in syms if s in symbol_metrics
                ),
                "pnl": sum(
                    symbol_metrics.get(s, {}).get("pnl", 0) for s in syms if s in symbol_metrics
                ),
            }
            for sector, syms in UNIVERSE_GROUPS.items()
        },
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.close()

    print("\n  Results saved:")
    print(f"     - Report: {report_path}")
    print(f"     - Equity: {eq_path}")
    print(f"     - Log: {LOG_DIR / 'v8_symbiotic_decisions.jsonl'}")

    print("\n" + "=" * 90)
    print("  OM TAT SAT - The Symbiotic Awakening Complete")
    print("=" * 90)

    return report


if __name__ == "__main__":
    run_v8_symbiotic_backtest()
