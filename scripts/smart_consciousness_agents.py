#!/usr/bin/env python3
"""
SMART Multi-Agent Consciousness System
Optimized: Batched API calls, Intelligent Caching, Hybrid Rule+LLM approach
"""

import hashlib
import json
import logging
import os
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Optional

import httpx
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ============================================================================
# SMART CACHE SYSTEM
# ============================================================================


class TattvaFingerprint:
    """Create a fingerprint of market state for intelligent caching"""

    @staticmethod
    def create(
        price: float,
        sma20: float,
        sma50: float,
        volatility: float,
        trend: str,
        volume: float,
    ) -> str:
        """Create a coarse-grained fingerprint for caching"""
        # Discretize values for cache hits on similar conditions
        _price_bucket = round(price / 1000) * 1000  # Round to nearest 1000
        sma_diff = round((price - sma50) / sma50 * 20) / 20  # Round to 5% buckets
        vol_bucket = round(volatility / 5) * 5  # 5% vol buckets

        fingerprint = f"{trend}_{sma_diff}_{vol_bucket}_{'high_vol' if volume > 1e6 else 'low_vol'}"
        return hashlib.md5(fingerprint.encode(), usedforsecurity=False).hexdigest()[:12]


class AgentCache:
    """LRU Cache for agent decisions with TTL"""

    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.cache: Dict[str, Dict] = {}
        self.timestamps: Dict[str, datetime] = {}
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self.access_order: deque = deque()

    def get(self, key: str) -> Optional[Dict]:
        """Get cached decision if not expired"""
        if key in self.cache:
            if datetime.now() - self.timestamps[key] < self.ttl:
                # Move to end (LRU)
                self.access_order.remove(key)
                self.access_order.append(key)
                return self.cache[key]
            else:
                # Expired
                self._remove(key)
        return None

    def set(self, key: str, value: Dict):
        """Cache a decision"""
        if len(self.cache) >= self.max_size:
            # Remove oldest
            oldest = self.access_order.popleft()
            self._remove(oldest)

        self.cache[key] = value
        self.timestamps[key] = datetime.now()
        self.access_order.append(key)

    def _remove(self, key: str):
        """Remove from cache"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)

    def stats(self) -> Dict:
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": getattr(self, "_hits", 0) / max(getattr(self, "_total", 1), 1),
        }


# ============================================================================
# SINGLE BATched PROMPT - All Agents in One Call
# ============================================================================

SMART_ENSEMBLE_PROMPT = """You are a council of 6 Vedic Trading Masters analyzing market conditions TOGETHER in one deliberation.

## THE COUNCIL MEMBERS:

**1. GURU (Jupiter) - Growth Master**
- Expert in: Expansion, bull markets, value appreciation
- Questions: Is this sustainable growth? Is Guru blessing this asset?

**2. SHANI (Saturn) - Risk Master**
- Expert in: Restrictions, bear markets, reality checks
- Questions: What's the downside? Is Rahu (illusion) present? Time to be cautious?

**3. SURYA (Sun) - Macro Master**
- Expert in: Big picture, economic cycles, systemic health
- Questions: Where are we in the cycle? Is the economy healthy?

**4. BUDHA (Mercury) - Execution Master**
- Expert in: Timing, position sizing, optimal entry/exit
- Questions: When to act? How much to allocate?

**5. MANGALA (Mars) - Protection Master**
- Expert in: Risk management, stop losses, capital preservation
- Questions: What can go wrong? How to protect capital?

**6. AHAMKARA (Orchestrator) - Balance Master**
- Expert in: Tri-Guna balance (Sattva/Rajas/Tamas)
- Questions: What's the overall balance? Which Guna dominates?

## THE 36 TATTVA FRAMEWORK:

**Elements (Pancha-bhutas):**
- Ether: Market sentiment space
- Air: Volatility/movement
- Fire: Momentum/breakouts
- Water: Liquidity/volume
- Earth: Fundamental value

**9 Navagrahas (Planetary Forces):**
- Surya: Macro vitality | Chandra: Sentiment cycles
- Mangala: Risk/protection | Budha: Execution/intelligence
- Guru: Growth/wisdom | Shukra: Value/attractiveness
- Shani: Discipline/restriction | Rahu: Illusion/bubbles | Ketu: Loss/exits

**3 Gunas (Qualities):**
- Sattva (Clarity): 0-1 score for clear perception
- Rajas (Action): 0-1 score for activity/drive
- Tamas (Inertia): 0-1 score for waiting/consolidation

## MARKET DATA:
```json
{market_context}
```

## PORTFOLIO STATE:
```json
{portfolio_context}
```

## YOUR TASK:
Each council member briefly shares their analysis (2-3 sentences), then the Orchestrator synthesizes and issues the FINAL TRADING DECISION.

Respond ONLY with this JSON structure:
{{
  "council_deliberation": {{
    "guru": {{"view": "bullish/bearish/neutral", "confidence": 0.0-1.0, "reasoning": "..."}},
    "shani": {{"view": "bullish/bearish/neutral", "confidence": 0.0-1.0, "reasoning": "..."}},
    "surya": {{"view": "bullish/bearish/neutral", "confidence": 0.0-1.0, "reasoning": "..."}},
    "budha": {{"view": "bullish/bearish/neutral", "confidence": 0.0-1.0, "timing": "now|soon|wait"}},
    "mangala": {{"risk_level": "low|medium|high", "max_position_pct": 5-20, "stop_recommended": true|false}},
    "ahamkara": {{"dominant_guna": "sattva|rajas|tamas", "guna_balance": {{"sattva": 0.0-1.0, "rajas": 0.0-1.0, "tamas": 0.0-1.0}}}}
  }},
  "final_decision": {{
    "action": "BUY|SELL|HOLD|SWITCH",
    "target_symbol": "BTC-EUR|ETH-EUR",
    "confidence": 0.0-1.0,
    "position_size_pct": 5.0-25.0,
    "strategy": "trend_following|mean_reversion|momentum|breakout",
    "stop_loss_pct": 2.0-10.0,
    "tattvas_aligned": ["guru", "agni", "surya"],
    "reasoning": "One sentence summary"
  }}
}}"""


# ============================================================================
# RULE-BASED SIGNAL GENERATOR (Fast, No API)
# ============================================================================


class RuleBasedSignals:
    """Generate fast rule-based signals as input to LLM"""

    @staticmethod
    def generate(df_slice: pd.DataFrame) -> Dict:
        """Generate technical signals from price data"""
        if len(df_slice) < 20:
            return {"error": "Insufficient data"}

        current = df_slice.iloc[-1]
        prev = df_slice.iloc[-2] if len(df_slice) > 1 else current

        # Moving averages
        sma20 = df_slice["close"].rolling(20).mean().iloc[-1]
        sma50 = df_slice["close"].rolling(min(50, len(df_slice))).mean().iloc[-1]

        # Trend
        trend = (
            "UP"
            if current["close"] > sma20 > sma50
            else "DOWN"
            if current["close"] < sma20 < sma50
            else "SIDEWAYS"
        )

        # RSI
        delta = df_slice["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]

        # Volatility
        volatility = df_slice["close"].pct_change().std() * (365**0.5) * 100

        # Bollinger Bands
        bb_middle = sma20
        bb_std = df_slice["close"].rolling(20).std().iloc[-1]
        bb_upper = bb_middle + 2 * bb_std
        bb_lower = bb_middle - 2 * bb_std
        bb_position = (current["close"] - bb_lower) / (bb_upper - bb_lower)

        # Volume trend
        vol_sma = df_slice["volume"].rolling(20).mean().iloc[-1]
        volume_spike = current["volume"] > vol_sma * 1.5

        # Candle patterns
        body = abs(current["close"] - current["open"])
        range_ = current["high"] - current["low"]
        body_pct = body / range_ if range_ > 0 else 0
        bullish = current["close"] > current["open"]

        # Generate signals
        signals = {
            "price_action": {
                "current_price": round(current["close"], 2),
                "sma20": round(sma20, 2),
                "sma50": round(sma50, 2),
                "trend": trend,
                "above_sma20": current["close"] > sma20,
                "above_sma50": current["close"] > sma50,
            },
            "momentum": {
                "rsi": round(rsi, 1),
                "rsi_signal": (
                    "oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral"
                ),
                "momentum": (
                    "positive" if current["close"] > prev["close"] else "negative"
                ),
            },
            "volatility": {
                "annualized_vol": round(volatility, 1),
                "bb_position": round(bb_position, 2),
                "bb_signal": (
                    "oversold"
                    if bb_position < 0.2
                    else "overbought"
                    if bb_position > 0.8
                    else "neutral"
                ),
            },
            "volume": {
                "current": int(current["volume"]),
                "spike": volume_spike,
                "trend": "increasing" if current["volume"] > vol_sma else "decreasing",
            },
            "candle": {
                "bullish": bullish,
                "body_pct": round(body_pct, 2),
                "pattern": RuleBasedSignals._candle_pattern(df_slice),
            },
            "composite_signal": RuleBasedSignals._composite_signal(
                trend, rsi, bb_position, bullish, volume_spike
            ),
        }

        return signals

    @staticmethod
    def _candle_pattern(df: pd.DataFrame) -> str:
        """Detect simple candlestick patterns"""
        if len(df) < 3:
            return "none"

        c = df.iloc[-1]
        p = df.iloc[-2]

        # Hammer/shooting star
        body = abs(c["close"] - c["open"])
        lower_shadow = min(c["close"], c["open"]) - c["low"]
        upper_shadow = c["high"] - max(c["close"], c["open"])

        if lower_shadow > body * 2 and upper_shadow < body:
            return "hammer" if c["close"] > c["open"] else "hanging_man"
        elif upper_shadow > body * 2 and lower_shadow < body:
            return "shooting_star"

        # Engulfing
        _p_body = abs(p["close"] - p["open"])
        if c["close"] > c["open"] and p["close"] < p["open"]:
            if c["close"] > p["open"] and c["open"] < p["close"]:
                return "bullish_engulfing"
        elif c["close"] < c["open"] and p["close"] > p["open"]:
            if c["open"] > p["close"] and c["close"] < p["open"]:
                return "bearish_engulfing"

        return "none"

    @staticmethod
    def _composite_signal(
        trend: str, rsi: float, bb_pos: float, bullish: bool, vol_spike: bool
    ) -> Dict:
        """Generate composite trading signal"""
        score = 0
        reasons = []

        if trend == "UP":
            score += 2
            reasons.append("uptrend")
        elif trend == "DOWN":
            score -= 2
            reasons.append("downtrend")

        if rsi < 30:
            score += 2
            reasons.append("oversold")
        elif rsi > 70:
            score -= 2
            reasons.append("overbought")

        if bb_pos < 0.2:
            score += 1
            reasons.append("bb_oversold")
        elif bb_pos > 0.8:
            score -= 1
            reasons.append("bb_overbought")

        if bullish:
            score += 1

        if vol_spike:
            score += 1 if bullish else -1
            reasons.append("volume_spike")

        signal = "BUY" if score >= 3 else "SELL" if score <= -3 else "HOLD"

        return {
            "score": score,
            "signal": signal,
            "strength": abs(score) / 5,
            "reasons": reasons,
        }


# ============================================================================
# SMART CONSCIOUSNESS ORCHESTRATOR
# ============================================================================


class SmartConsciousnessOrchestrator:
    """
    Smart orchestrator that:
    1. Uses rule-based signals as input
    2. Caches decisions based on Tattva fingerprint
    3. Makes ONE batched API call per analysis
    4. Falls back to rule-based if API fails
    """

    def __init__(self):
        self.cache = AgentCache(max_size=500, ttl_hours=48)
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com"
        self.model = "deepseek-chat"  # Fast model
        self.rule_engine = RuleBasedSignals()

        # Stats
        self.api_calls = 0
        self.cache_hits = 0

    async def analyze(
        self, symbol: str, df_slice: pd.DataFrame, portfolio: Dict
    ) -> Dict:
        """
        Smart analysis with caching and batching
        """
        # Step 1: Generate rule-based signals (fast)
        rule_signals = self.rule_engine.generate(df_slice)

        # Step 2: Create Tattva fingerprint for caching
        current = df_slice.iloc[-1]
        sma20 = (
            df_slice["close"].rolling(20).mean().iloc[-1]
            if len(df_slice) >= 20
            else current["close"]
        )
        sma50 = (
            df_slice["close"].rolling(50).mean().iloc[-1]
            if len(df_slice) >= 50
            else current["close"]
        )
        volatility = (
            df_slice["close"].pct_change().std() * (365**0.5) * 100
            if len(df_slice) > 1
            else 50
        )
        trend = rule_signals["price_action"]["trend"]

        fingerprint = TattvaFingerprint.create(
            current["close"], sma20, sma50, volatility, trend, current["volume"]
        )
        cache_key = f"{symbol}_{fingerprint}"

        # Step 3: Check cache
        cached = self.cache.get(cache_key)
        if cached:
            self.cache_hits += 1
            logger.debug(f"Cache hit for {symbol} ({self.cache_hits} total hits)")
            return {**cached, "cache_hit": True, "rule_signals": rule_signals}

        # Step 4: Build context for LLM
        market_context = {
            "symbol": symbol,
            "timestamp": str(df_slice.index[-1]),
            "price": round(current["close"], 2),
            "change_24h": (
                round(
                    (current["close"] - df_slice.iloc[-2]["close"])
                    / df_slice.iloc[-2]["close"]
                    * 100,
                    2,
                )
                if len(df_slice) > 1
                else 0
            ),
            "technical_signals": rule_signals,
            "recent_candles": len(df_slice),
        }

        portfolio_context = {
            "cash_eur": portfolio.get("cash", 100000),
            "current_positions": list(portfolio.get("positions", {}).keys()),
            "total_exposure": sum(
                p.get("value", 0) for p in portfolio.get("positions", {}).values()
            ),
        }

        # Step 5: Call LLM with batched prompt
        try:
            decision = await self._call_ensemble_llm(market_context, portfolio_context)
            self.api_calls += 1

            # Cache the decision
            self.cache.set(cache_key, decision)

            return {**decision, "cache_hit": False, "rule_signals": rule_signals}

        except Exception as e:
            logger.error(f"LLM call failed, using rule-based fallback: {e}")
            # Fallback to rule-based
            fallback = self._rule_based_fallback(rule_signals, symbol)
            return {**fallback, "llm_error": str(e), "rule_signals": rule_signals}

    async def _call_ensemble_llm(
        self, market_context: Dict, portfolio_context: Dict
    ) -> Dict:
        """Make single batched API call for all agents"""

        # Convert numpy types to Python types for JSON serialization
        def convert_to_serializable(obj):
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(i) for i in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, pd.Timestamp):
                return str(obj)
            return obj

        market_context = convert_to_serializable(market_context)
        portfolio_context = convert_to_serializable(portfolio_context)

        prompt = SMART_ENSEMBLE_PROMPT.format(
            market_context=json.dumps(market_context, indent=2),
            portfolio_context=json.dumps(portfolio_context, indent=2),
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = [
            {
                "role": "system",
                "content": "You are a Vedic trading council. Respond ONLY with valid JSON.",
            },
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1500,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload
            )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # Extract JSON
                try:
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        result = json.loads(content[json_start:json_end])
                        return result
                    else:
                        raise ValueError("No JSON in response")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}")
                    raise
            else:
                raise Exception(f"API error: {response.status_code}")

    def _rule_based_fallback(self, signals: Dict, symbol: str) -> Dict:
        """Fallback decision based on rule-based signals"""
        composite = signals.get("composite_signal", {})

        # Simple guna assignment based on RSI
        rsi = signals.get("momentum", {}).get("rsi", 50)
        if rsi > 60:
            guna = "rajas"
            guna_scores = {"sattva": 0.3, "rajas": 0.6, "tamas": 0.1}
        elif rsi < 40:
            guna = "tamas"
            guna_scores = {"sattva": 0.2, "rajas": 0.3, "tamas": 0.5}
        else:
            guna = "sattva"
            guna_scores = {"sattva": 0.6, "rajas": 0.2, "tamas": 0.2}

        return {
            "council_deliberation": {
                "ahamkara": {"dominant_guna": guna, "guna_balance": guna_scores},
                "fallback": True,
            },
            "final_decision": {
                "action": composite.get("signal", "HOLD"),
                "target_symbol": symbol,
                "confidence": composite.get("strength", 0.5),
                "position_size_pct": 10.0,
                "strategy": "rule_based_fallback",
                "reasoning": f"Rule-based: {', '.join(composite.get('reasons', []))}",
            },
        }

    def get_stats(self) -> Dict:
        """Get orchestrator stats"""
        return {
            "api_calls": self.api_calls,
            "cache_hits": self.cache_hits,
            "cache_size": len(self.cache.cache),
            "cache_hit_rate": self.cache_hits
            / max(self.api_calls + self.cache_hits, 1),
        }
