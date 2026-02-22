"""
Trading Signals Translator
Converts complex Vedic astrology data into actionable trading signals for agents.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SignalStrength(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class TimeFrame(Enum):
    SCALP = "scalp"  # Minutes
    INTRADAY = "intraday"  # Hours
    SWING = "swing"  # Days
    POSITION = "position"  # Weeks
    LONG_TERM = "long_term"  # Months


@dataclass
class TradingSignal:
    """Structured trading signal for agents."""

    timestamp: str
    symbol: str
    signal: SignalStrength
    confidence: float  # 0-100
    timeframe: TimeFrame
    entry_price_range: Optional[tuple]  # (min, max)
    stop_loss: Optional[float]
    take_profit: Optional[float]

    # Astrological basis
    primary_factors: List[str]
    supporting_factors: List[str]
    warning_factors: List[str]

    # Detailed context
    dasha_context: str
    transit_context: str
    strength_score: float  # 0-100

    # Action guidance
    recommended_action: str
    risk_level: str  # low/medium/high
    position_size_suggestion: str  # small/medium/large

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "symbol": self.symbol,
            "signal": self.signal.value,
            "confidence": self.confidence,
            "timeframe": self.timeframe.value,
            "entry_price_range": self.entry_price_range,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "primary_factors": self.primary_factors,
            "supporting_factors": self.supporting_factors,
            "warning_factors": self.warning_factors,
            "dasha_context": self.dasha_context,
            "transit_context": self.transit_context,
            "strength_score": self.strength_score,
            "recommended_action": self.recommended_action,
            "risk_level": self.risk_level,
            "position_size_suggestion": self.position_size_suggestion,
        }

    def to_llm_prompt(self) -> str:
        """Convert signal to LLM-friendly prompt format."""
        return f"""
TRADING SIGNAL GENERATED

Asset: {self.symbol}
Signal: {self.signal.value.upper()} (Confidence: {self.confidence}%)
Timeframe: {self.timeframe.value}
Strength Score: {self.strength_score}/100

ASTROLOGICAL BASIS:
{self.dasha_context}

{self.transit_context}

PRIMARY FACTORS:
{chr(10).join(['• ' + f for f in self.primary_factors])}

SUPPORTING FACTORS:
{chr(10).join(['• ' + f for f in self.supporting_factors]) if self.supporting_factors else 'None'}

WARNINGS:
{chr(10).join(['⚠ ' + f for f in self.warning_factors]) if self.warning_factors else 'None'}

RECOMMENDED ACTION:
{self.recommended_action}

Risk Level: {self.risk_level.upper()}
Suggested Position Size: {self.position_size_suggestion.upper()}
"""


class TradingSignalGenerator:
    """
    Generates actionable trading signals from Vedic astrology data.
    Translates complex astrology into agent-understandable instructions.
    """

    def __init__(self):
        self.sign_strength_weights = {
            "exalted": 1.0,
            "own_sign": 0.8,
            "friend_sign": 0.6,
            "neutral": 0.4,
            "enemy_sign": 0.2,
            "debilitated": 0.0,
        }

    def generate_signal(
        self,
        symbol: str,
        kundli: Dict[str, Any],
        dasha: Any,
        ashtaka: Dict[str, Any],
        yogas: List[Any],
        avastas: Dict[str, Any],
        sahams: Dict[str, float],
        transits: Dict[str, Any],
        pancha_pakshi: Any,
        muhurtha: Any,
        current_price: Optional[float] = None,
    ) -> TradingSignal:
        """
        Generate comprehensive trading signal from all astrological data.
        """

        # Calculate base scores
        dasha_score = self._calculate_dasha_score(dasha)
        yoga_score = self._calculate_yoga_score(yogas)
        avasta_score = self._calculate_avasta_score(avastas)
        transit_score = self._calculate_transit_score(transits, ashtaka)
        sahams_score = self._calculate_sahams_score(sahams, transits)
        muhurtha_score = muhurtha.rating if muhurtha else 5.0
        pancha_score = pancha_pakshi.strength if pancha_pakshi else 0.5

        # Weighted total (weights sum to 1.0)
        weights = {
            "dasha": 0.25,
            "yoga": 0.15,
            "avasta": 0.15,
            "transit": 0.20,
            "sahams": 0.15,
            "muhurtha": 0.05,
            "pancha": 0.05,
        }

        total_score = (
            dasha_score * weights["dasha"]
            + yoga_score * weights["yoga"]
            + avasta_score * weights["avasta"]
            + transit_score * weights["transit"]
            + sahams_score * weights["sahams"]
            + (muhurtha_score / 10) * weights["muhurtha"]
            + pancha_score * weights["pancha"]
        ) * 100  # Scale to 0-100

        # Determine signal
        signal = self._score_to_signal(total_score)

        # Generate contexts
        dasha_context = self._generate_dasha_context(dasha)
        transit_context = self._generate_transit_context(transits, ashtaka)

        # Collect factors
        primary, supporting, warnings = self._collect_all_factors(
            dasha, yogas, avastas, transits, sahams, muhurtha, pancha_pakshi
        )

        # Determine action
        action = self._generate_recommended_action(
            signal, total_score, primary, warnings
        )

        # Risk assessment
        risk_level = self._assess_risk_level(total_score, warnings, avastas)

        # Position sizing
        position_size = self._suggest_position_size(total_score, risk_level, warnings)

        return TradingSignal(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            signal=signal,
            confidence=min(100, max(0, total_score)),
            timeframe=self._determine_timeframe(dasha),
            entry_price_range=self._calculate_entry_range(current_price, signal),
            stop_loss=self._calculate_stop_loss(current_price, signal, total_score),
            take_profit=self._calculate_take_profit(current_price, signal, total_score),
            primary_factors=primary,
            supporting_factors=supporting,
            warning_factors=warnings,
            dasha_context=dasha_context,
            transit_context=transit_context,
            strength_score=total_score,
            recommended_action=action,
            risk_level=risk_level,
            position_size_suggestion=position_size,
        )

    def _calculate_dasha_score(self, dasha: Any) -> float:
        """Score based on current Dasha lords."""
        if not dasha:
            return 0.5

        benefic_planets = ["Jupiter", "Venus", "Mercury", "Moon"]
        malefic_planets = ["Saturn", "Mars", "Rahu", "Ketu"]

        score = 0.5

        # Mahadasha weight: 50%
        if dasha.mahadasha_lord in benefic_planets:
            score += 0.25
        elif dasha.mahadasha_lord in malefic_planets:
            score -= 0.25

        # Antardasha weight: 30%
        if dasha.antardasha_lord in benefic_planets:
            score += 0.15
        elif dasha.antardasha_lord in malefic_planets:
            score -= 0.15

        # Pratyantardasha weight: 20%
        if dasha.pratyantardasha_lord in benefic_planets:
            score += 0.10
        elif dasha.pratyantardasha_lord in malefic_planets:
            score -= 0.10

        return max(0, min(1, score))

    def _calculate_yoga_score(self, yogas: List[Any]) -> float:
        """Score based on present Yogas."""
        if not yogas:
            return 0.5

        # High-value trading yogas
        excellent_yogas = [
            "Gaja Kesari Yoga",
            "Hamsa Yoga",
            "Lakshmi Yoga",
            "Dhana Yoga",
        ]
        good_yogas = ["Bhadra Yoga", "Malavya Yoga", "Budha-Aditya Yoga"]
        caution_yogas = ["Chandra-Mangala Yoga"]

        score = 0.5

        for yoga in yogas:
            if yoga.name in excellent_yogas:
                score += 0.2 * yoga.strength
            elif yoga.name in good_yogas:
                score += 0.1 * yoga.strength
            elif yoga.name in caution_yogas:
                score -= 0.1 * yoga.strength

        return max(0, min(1, score))

    def _calculate_avasta_score(self, avastas: Dict[str, Any]) -> float:
        """Score based on planetary Avastas."""
        if not avastas:
            return 0.5

        total_strength = sum(a.strength_percent for a in avastas.values())
        avg_strength = total_strength / len(avastas) if avastas else 50

        return avg_strength / 100

    def _calculate_transit_score(
        self, transits: Dict[str, Any], ashtaka: Dict[str, Any]
    ) -> float:
        """Score based on current transits."""
        if not transits or not transits.get("current_positions"):
            return 0.5

        positions = transits["current_positions"]

        # Count favorable vs unfavorable
        favorable = 0
        unfavorable = 0

        for planet, pos in positions.items():
            if pos.get("exalted"):
                favorable += 2
            elif pos.get("debilitated"):
                unfavorable += 2
            elif pos.get("is_favorable"):
                favorable += 1
            else:
                unfavorable += 1

        total = favorable + unfavorable
        if total == 0:
            return 0.5

        return favorable / total

    def _calculate_sahams_score(
        self, sahams: Dict[str, float], transits: Dict[str, Any]
    ) -> float:
        """Score based on Saham transits."""
        # Check if transits are favorable to Artha and Labha Sahams
        # This is a simplified version
        return 0.6  # Neutral default

    def _score_to_signal(self, score: float) -> SignalStrength:
        """Convert numerical score to signal."""
        if score >= 80:
            return SignalStrength.STRONG_BUY
        elif score >= 60:
            return SignalStrength.BUY
        elif score >= 40:
            return SignalStrength.HOLD
        elif score >= 20:
            return SignalStrength.SELL
        else:
            return SignalStrength.STRONG_SELL

    def _generate_dasha_context(self, dasha: Any) -> str:
        """Generate human-readable Dasha context."""
        if not dasha:
            return "No Dasha information available."

        contexts = {
            "Jupiter": "Jupiter Mahadasha brings wisdom, expansion, and prosperity. Good for long-term investments.",
            "Venus": "Venus Mahadasha brings luxury, relationships, and financial growth. Favorable for trading.",
            "Mercury": "Mercury Mahadasha brings communication, analysis, and quick decisions. Good for day trading.",
            "Sun": "Sun Mahadasha brings authority and power. Moderate for trading, focus on large caps.",
            "Moon": "Moon Mahadasha brings emotions and fluctuations. Caution advised, volatile period.",
            "Mars": "Mars Mahadasha brings energy and aggression. Good for bold moves but manage risk.",
            "Saturn": "Saturn Mahadasha brings discipline and restrictions. Focus on long-term, conservative strategies.",
            "Rahu": "Rahu Mahadasha brings illusion and sudden changes. High volatility, unpredictable markets.",
            "Ketu": "Ketu Mahadasha brings detachment and spiritual growth. Not favorable for material gains.",
        }

        main_context = contexts.get(dasha.mahadasha_lord, "Mixed influences.")

        return f"""
Current Dasha Period:
• Mahadasha (Major): {dasha.mahadasha_lord} ({dasha.mahadasha_start.strftime('%Y-%m-%d')} to {dasha.mahadasha_end.strftime('%Y-%m-%d')})
• Antardasha (Sub): {dasha.antardasha_lord}
• Pratyantardasha (Sub-sub): {dasha.pratyantardasha_lord}

{main_context}
        """.strip()

    def _generate_transit_context(
        self, transits: Dict[str, Any], ashtaka: Dict[str, Any]
    ) -> str:
        """Generate human-readable transit context."""
        if not transits:
            return "No transit information available."

        positions = transits.get("current_positions", {})

        # Count exalted/debilitated
        exalted = [p for p, pos in positions.items() if pos.get("exalted")]
        debilitated = [p for p, pos in positions.items() if pos.get("debilitated")]
        retrograde = [p for p, pos in positions.items() if pos.get("retrograde")]

        context_parts = []

        if exalted:
            context_parts.append(f"Exalted planets (strong): {', '.join(exalted)}")
        if debilitated:
            context_parts.append(
                f"Debilitated planets (weak): {', '.join(debilitated)}"
            )
        if retrograde:
            context_parts.append(
                f"Retrograde planets (review/rethink): {', '.join(retrograde)}"
            )

        return (
            "Current Transits:\n• " + "\n• ".join(context_parts)
            if context_parts
            else "Transits are neutral."
        )

    def _collect_all_factors(
        self, dasha, yogas, avastas, transits, sahams, muhurtha, pancha_pakshi
    ):
        """Collect all factors into primary, supporting, and warnings."""
        primary = []
        supporting = []
        warnings = []

        # Dasha factors
        if dasha:
            if dasha.mahadasha_lord in ["Jupiter", "Venus"]:
                primary.append(f"Benefic Mahadasha lord: {dasha.mahadasha_lord}")
            elif dasha.mahadasha_lord in ["Saturn", "Rahu", "Ketu"]:
                warnings.append(f"Malefic Mahadasha lord: {dasha.mahadasha_lord}")

        # Yoga factors
        if yogas:
            for yoga in yogas[:3]:  # Top 3 yogas
                if yoga.strength > 0.7:
                    primary.append(f"Strong {yoga.name}: {yoga.trading_significance}")
                elif yoga.strength > 0.4:
                    supporting.append(f"Present {yoga.name}")

        # Avasta factors
        if avastas:
            strong_planets = [
                a.planet for a in avastas.values() if a.strength_percent > 70
            ]
            weak_planets = [
                a.planet for a in avastas.values() if a.strength_percent < 30
            ]

            if strong_planets:
                supporting.append(f"Strong planets: {', '.join(strong_planets)}")
            if weak_planets:
                warnings.append(f"Weak planets: {', '.join(weak_planets)}")

        # Transit factors
        if transits:
            if transits.get("retrograde_count", 0) > 3:
                warnings.append(
                    f"Many retrograde planets ({transits['retrograde_count']}): Expect delays and reversals"
                )

        # Sahams
        if sahams:
            supporting.append("Financial Sahams calculated for wealth indicators")

        # Muhurtha
        if muhurtha:
            if muhurtha.is_favorable:
                supporting.append(
                    f"Favorable Muhurtha: {muhurtha.tithi} ({muhurtha.rating}/10)"
                )
            else:
                warnings.append(
                    f"Unfavorable Muhurtha: {muhurtha.tithi} ({muhurtha.rating}/10)"
                )

        # Pancha Pakshi
        if pancha_pakshi:
            if pancha_pakshi.is_favorable_period:
                supporting.append(
                    f"Favorable Pancha Pakshi activity: {pancha_pakshi.current_activity}"
                )
            else:
                warnings.append(
                    f"Unfavorable Pancha Pakshi activity: {pancha_pakshi.current_activity}"
                )

        return primary, supporting, warnings

    def _generate_recommended_action(
        self, signal: SignalStrength, score: float, primary: List, warnings: List
    ) -> str:
        """Generate specific action recommendation."""

        actions = {
            SignalStrength.STRONG_BUY: "Enter LONG position immediately. Multiple strong astrological factors align. Consider larger position size.",
            SignalStrength.BUY: "Enter LONG position with standard risk management. Positive astrological environment.",
            SignalStrength.HOLD: "Maintain current positions. No clear astrological direction. Wait for better entry.",
            SignalStrength.SELL: "Consider reducing positions or entering SHORT. Negative astrological factors present.",
            SignalStrength.STRONG_SELL: "Enter SHORT position or exit all LONGs immediately. Strong negative astrological alignment.",
        }

        base_action = actions.get(signal, "HOLD")

        if warnings:
            base_action += f"\n\nCAUTION: {len(warnings)} warning factors present. Use tight stop-loss."

        return base_action

    def _assess_risk_level(self, score: float, warnings: List, avastas: Dict) -> str:
        """Assess risk level."""
        risk_score = 0

        # Score-based risk
        if score > 75 or score < 25:
            risk_score += 1  # Extreme scores can mean volatility
        else:
            risk_score += 2

        # Warning-based risk
        risk_score += len(warnings) * 0.5

        # Retrograde risk
        if avastas:
            retro_count = sum(1 for a in avastas.values() if a.is_retrograde)
            risk_score += retro_count * 0.3

        if risk_score < 2:
            return "low"
        elif risk_score < 4:
            return "medium"
        else:
            return "high"

    def _suggest_position_size(
        self, score: float, risk_level: str, warnings: List
    ) -> str:
        """Suggest position size based on confidence and risk."""
        if risk_level == "high":
            return "small"

        if score > 80:
            return "large"
        elif score > 60:
            return "medium"
        else:
            return "small"

    def _determine_timeframe(self, dasha: Any) -> TimeFrame:
        """Determine optimal trading timeframe based on Dasha."""
        if not dasha:
            return TimeFrame.SWING

        # Fast-moving dasha lords = shorter timeframes
        fast_planets = ["Moon", "Mercury"]
        slow_planets = ["Jupiter", "Saturn"]

        if dasha.mahadasha_lord in fast_planets:
            return TimeFrame.INTRADAY
        elif dasha.mahadasha_lord in slow_planets:
            return TimeFrame.POSITION
        else:
            return TimeFrame.SWING

    def _calculate_entry_range(
        self, current_price: Optional[float], signal: SignalStrength
    ) -> Optional[tuple]:
        """Calculate suggested entry price range."""
        if not current_price:
            return None

        if signal in [SignalStrength.STRONG_BUY, SignalStrength.BUY]:
            # Buy slightly below current or at current
            return (current_price * 0.98, current_price * 1.0)
        elif signal in [SignalStrength.STRONG_SELL, SignalStrength.SELL]:
            # Sell slightly above current or at current
            return (current_price * 1.0, current_price * 1.02)
        else:
            return None

    def _calculate_stop_loss(
        self, current_price: Optional[float], signal: SignalStrength, score: float
    ) -> Optional[float]:
        """Calculate suggested stop-loss."""
        if not current_price:
            return None

        # Base stop-loss percentage based on score (higher score = tighter stop)
        if score > 70:
            stop_pct = 0.02  # 2%
        elif score > 50:
            stop_pct = 0.03  # 3%
        else:
            stop_pct = 0.05  # 5%

        if signal in [SignalStrength.STRONG_BUY, SignalStrength.BUY]:
            return current_price * (1 - stop_pct)
        elif signal in [SignalStrength.STRONG_SELL, SignalStrength.SELL]:
            return current_price * (1 + stop_pct)
        else:
            return None

    def _calculate_take_profit(
        self, current_price: Optional[float], signal: SignalStrength, score: float
    ) -> Optional[float]:
        """Calculate suggested take-profit."""
        if not current_price:
            return None

        # Risk:Reward ratio based on score
        if score > 70:
            reward_ratio = 3  # 1:3
        elif score > 50:
            reward_ratio = 2  # 1:2
        else:
            reward_ratio = 1.5  # 1:1.5

        stop_loss = self._calculate_stop_loss(current_price, signal, score)
        if not stop_loss:
            return None

        risk = abs(current_price - stop_loss)

        if signal in [SignalStrength.STRONG_BUY, SignalStrength.BUY]:
            return current_price + (risk * reward_ratio)
        elif signal in [SignalStrength.STRONG_SELL, SignalStrength.SELL]:
            return current_price - (risk * reward_ratio)
        else:
            return None


class AgentPromptBuilder:
    """
    Builds prompts for LLM agents with astrological context.
    """

    @staticmethod
    def build_trading_prompt(signal: TradingSignal, market_context: str = "") -> str:
        """Build comprehensive prompt for trading agent."""

        return f"""You are an advanced Vedic Astrology Trading Agent analyzing {signal.symbol}.

ASTROLOGICAL TRADING SIGNAL
===========================
{signal.to_llm_prompt()}

{market_context}

YOUR TASK:
1. Review the astrological signal above
2. Consider the primary factors, supporting factors, and warnings
3. Make a trading decision: ENTER, HOLD, or EXIT
4. Provide your reasoning based on the astrological data

RESPONSE FORMAT:
{{
    "decision": "ENTER_LONG|ENTER_SHORT|HOLD|EXIT",
    "confidence": 0-100,
    "reasoning": "Your astrological analysis",
    "risk_assessment": "low|medium|high",
    "suggested_position_size": "small|medium|large",
    "timeframe": "scalp|intraday|swing|position",
    "astrological_notes": "Key astrological observations"
}}

Provide ONLY the JSON response.
"""

    @staticmethod
    def build_consciousness_prompt(
        kundli: Dict[str, Any], yogas: List[Any], dasha: Any, transits: Dict[str, Any]
    ) -> str:
        """Build prompt for consciousness/trading psychology agent."""

        yoga_summary = (
            "\n".join([f"- {y.name}: {y.trading_significance}" for y in yogas[:5]])
            if yogas
            else "No major yogas"
        )

        return f"""You are a Vedic Consciousness Agent analyzing the energetic quality of this trading moment.

CURRENT ASTROLOGICAL CONFIGURATION
===================================
Lagna (Rising): {kundli.get('lagna', 'Unknown')}
Moon Sign: {kundli.get('planets', {}).get('Moon', {}).get('sign', 'Unknown')}
Moon Nakshatra: {kundli.get('planets', {}).get('Moon', {}).get('nakshatra', 'Unknown')}

ACTIVE YOGAS (Planetary Combinations):
{yoga_summary}

CURRENT DASHA:
Mahadasha: {dasha.mahadasha_lord if dasha else 'Unknown'}
Antardasha: {dasha.antardasha_lord if dasha else 'Unknown'}

ENERGETIC ASSESSMENT:
- Dasha Quality: {dasha.mahadasha_lord if dasha else 'Unknown'} brings {'expansion and wisdom' if dasha and dasha.mahadasha_lord == 'Jupiter' else 'discipline and structure' if dasha and dasha.mahadasha_lord == 'Saturn' else 'transformation' if dasha and dasha.mahadasha_lord == 'Rahu' else 'mixed energies'}
- Guna Balance: Analyze Sattva/Rajas/Tamas
- Mental Clarity: Based on Moon and Mercury

YOUR TASK:
Provide a CONSCIOUSNESS ASSESSMENT for trading:
1. What is the energetic quality of this moment?
2. Is this a time for action or patience?
3. What mental/emotional state should the trader cultivate?
4. Any spiritual/psychological warnings?

RESPOND with wisdom and clarity.
"""
