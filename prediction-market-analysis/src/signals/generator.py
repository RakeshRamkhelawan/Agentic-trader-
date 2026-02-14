"""
Signal Generator Engine
Generates market signals from analysis results.
"""
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """Signal types."""
    SPREAD_OPPORTUNITY = "spread_opportunity"
    VOLUME_SPIKE = "volume_spike"
    TREND_REVERSAL = "trend_reversal"
    ARBITRAGE = "arbitrage"
    ANOMALY = "anomaly"
    LIQUIDITY_WARNING = "liquidity_warning"
    CORRELATION_SHIFT = "correlation_shift"


class SignalCategory(str, Enum):
    """Signal categories."""
    POLITICS = "politics"
    ENTERTAINMENT = "entertainment"
    SPORTS = "sports"
    FINANCE = "finance"
    OTHER = "other"


@dataclass
class SignalIndicator:
    """Individual signal indicator."""
    name: str
    value: float
    threshold: float
    breached: bool
    interpretation: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class MarketSignal:
    """Generated market signal."""
    signal_id: str
    market: str
    symbol: str
    category: SignalCategory
    signal_type: SignalType
    confidence: float  # 0-100
    score: float  # Overall signal strength
    indicators: List[SignalIndicator]
    recommendation: str
    created_at: datetime
    expires_at: Optional[datetime]
    metadata: Dict
    
    def to_dict(self) -> Dict:
        """Convert to dictionary (JSON serializable)."""
        return {
            "signal_id": self.signal_id,
            "market": self.market,
            "symbol": self.symbol,
            "category": self.category.value,
            "signal_type": self.signal_type.value,
            "confidence": self.confidence,
            "score": self.score,
            "indicators": [ind.to_dict() for ind in self.indicators],
            "recommendation": self.recommendation,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }


class SignalGenerator:
    """
    Generates market signals from analysis results.
    
    Combines findings from multiple analyzers (spread, volume, statistical)
    and generates actionable signals for traders.
    
    Usage:
        generator = SignalGenerator()
        signal = generator.generate_spread_signal(
            market="Trump 2024",
            spreads_metrics=metrics,
            confidence_boost=10
        )
    """
    
    def __init__(self):
        """Initialize signal generator."""
        self._signal_counter = 0
    
    def _generate_signal_id(self, market: str) -> str:
        """Generate unique signal ID."""
        self._signal_counter += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"sig_{market.replace(' ', '_')}_{timestamp}_{self._signal_counter}"
    
    def generate_spread_signal(
        self,
        market: str,
        symbol: str,
        spread_metrics: Dict,
        category: SignalCategory = SignalCategory.POLITICS,
        confidence_boost: float = 0.0
    ) -> Optional[MarketSignal]:
        """
        Generate signal from spread analysis.
        
        Args:
            market: Market name
            symbol: Trading symbol
            spread_metrics: Dict with spread analysis metrics
            category: Market category
            confidence_boost: Additional confidence percentage
        
        Returns:
            MarketSignal if threshold breached, else None
        """
        mean_spread = spread_metrics.get("mean_spread", 0)
        spread_pct = spread_metrics.get("spread_percentage_mean", 0)
        liquidity_score = spread_metrics.get("liquidity_score", 0)
        
        # Thresholds
        TIGHT_SPREAD_THRESHOLD = 0.02  # 2% spread is tight
        HIGH_LIQUIDITY_THRESHOLD = 70
        
        spread_breached = spread_pct < TIGHT_SPREAD_THRESHOLD
        liquidity_breached = liquidity_score > HIGH_LIQUIDITY_THRESHOLD
        
        signal_triggered = spread_breached or liquidity_breached
        
        if not signal_triggered:
            return None
        
        # Calculate confidence
        spread_confidence = max(0, 100 * (1 - spread_pct / 0.05))
        liquidity_confidence = liquidity_score
        confidence = (spread_confidence + liquidity_confidence) / 2
        confidence += confidence_boost
        confidence = min(100, max(0, confidence))
        
        # Indicators
        indicators = [
            SignalIndicator(
                name="Bid-Ask Spread",
                value=spread_pct,
                threshold=TIGHT_SPREAD_THRESHOLD,
                breached=spread_breached,
                interpretation=f"Spread of {spread_pct:.2f}% (tight < 2%)"
            ),
            SignalIndicator(
                name="Liquidity Score",
                value=liquidity_score,
                threshold=HIGH_LIQUIDITY_THRESHOLD,
                breached=liquidity_breached,
                interpretation=f"High liquidity score: {liquidity_score:.1f}/100"
            ),
        ]
        
        # Recommendation
        recommendation = "Good opportunity for arbitrage or market making"
        
        return MarketSignal(
            signal_id=self._generate_signal_id(market),
            market=market,
            symbol=symbol,
            category=category,
            signal_type=SignalType.SPREAD_OPPORTUNITY,
            confidence=confidence,
            score=min(100, spread_pct * 100 + liquidity_score),
            indicators=indicators,
            recommendation=recommendation,
            created_at=datetime.now(timezone.utc),
            expires_at=None,
            metadata={
                "analyzer": "MakerTakerAnalyzer",
                "metrics": spread_metrics,
            }
        )
    
    def generate_volume_signal(
        self,
        market: str,
        symbol: str,
        volume_metrics: Dict,
        category: SignalCategory = SignalCategory.POLITICS,
        confidence_boost: float = 0.0
    ) -> Optional[MarketSignal]:
        """
        Generate signal from volume analysis.
        
        Args:
            market: Market name
            symbol: Trading symbol
            volume_metrics: Dict with volume analysis metrics
            category: Market category
            confidence_boost: Additional confidence percentage
        
        Returns:
            MarketSignal if spike detected, else None
        """
        volume_trend = volume_metrics.get("volume_trend", "stable")
        trend_strength = volume_metrics.get("trend_strength", 0)
        volume_concentration = volume_metrics.get("volume_concentration", 0)
        trade_count = volume_metrics.get("trades_count", 0)
        
        # Detect trends
        trend_breached = trend_strength > 0.6
        concentration_breached = volume_concentration < 30  # Distributed volume good
        
        signal_triggered = trend_breached and trade_count > 20
        
        if not signal_triggered:
            return None
        
        # Calculate confidence
        trend_confidence = trend_strength * 100
        activity_confidence = min(100, trade_count / 2)  # 50+ trades = 100%
        confidence = (trend_confidence + activity_confidence) / 2
        confidence += confidence_boost
        confidence = min(100, max(0, confidence))
        
        # Determine signal type
        if volume_trend == "increasing":
            signal_type = SignalType.VOLUME_SPIKE
            recommendation = "Increasing volume indicates growing interest"
        elif volume_trend == "decreasing":
            signal_type = SignalType.LIQUIDITY_WARNING
            recommendation = "Decreasing volume may indicate dying market"
        else:
            signal_type = SignalType.ANOMALY
            recommendation = "Unusual volume pattern detected"
        
        indicators = [
            SignalIndicator(
                name="Volume Trend",
                value=trend_strength,
                threshold=0.6,
                breached=trend_breached,
                interpretation=f"{volume_trend.capitalize()} trend (strength: {trend_strength:.2f})"
            ),
            SignalIndicator(
                name="Volume Concentration",
                value=volume_concentration,
                threshold=50,
                breached=not concentration_breached,
                interpretation=f"Top 10% trades: {volume_concentration:.1f}% of total"
            ),
        ]
        
        return MarketSignal(
            signal_id=self._generate_signal_id(market),
            market=market,
            symbol=symbol,
            category=category,
            signal_type=signal_type,
            confidence=confidence,
            score=trend_strength * 100,
            indicators=indicators,
            recommendation=recommendation,
            created_at=datetime.now(timezone.utc),
            expires_at=None,
            metadata={
                "analyzer": "VolumeTrendsAnalyzer",
                "metrics": volume_metrics,
            }
        )
    
    def generate_statistical_signal(
        self,
        market: str,
        symbol: str,
        test_results: Dict,
        category: SignalCategory = SignalCategory.POLITICS,
        confidence_boost: float = 0.0
    ) -> Optional[MarketSignal]:
        """
        Generate signal from statistical test results.
        
        Args:
            market: Market name
            symbol: Trading symbol
            test_results: Dict with statistical test results
            category: Market category
            confidence_boost: Additional confidence percentage
        
        Returns:
            MarketSignal if significant pattern found, else None
        """
        # Check for mean reversion signal
        mean_reversion_result = test_results.get("mean_reversion_test")
        stationarity_result = test_results.get("stationarity_test")
        
        if not mean_reversion_result:
            return None
        
        # Both should indicate mean reversion for strong signal
        mr_significant = mean_reversion_result.get("significant", False)
        stat_significant = stationarity_result.get("significant", False) if stationarity_result else False
        
        signal_triggered = mr_significant and stat_significant
        
        if not signal_triggered:
            return None
        
        # Calculate confidence based on effect sizes
        mr_strength = mean_reversion_result.get("effect_size", 0)
        mr_pvalue = mean_reversion_result.get("p_value", 1.0)
        
        # Confidence based on statistical significance
        confidence = max(0, 100 * (1 - mr_pvalue))
        confidence = min(100, max(0, confidence + confidence_boost))
        
        indicators = [
            SignalIndicator(
                name="Mean Reversion",
                value=mr_strength if mr_strength else 0,
                threshold=5.0,
                breached=mr_significant,
                interpretation=f"Mean reversion detected (p={mr_pvalue:.4f})"
            ),
            SignalIndicator(
                name="Stationarity",
                value=stationarity_result.get("statistic", 0) if stationarity_result else 0,
                threshold=0.0,
                breached=stat_significant,
                interpretation="Price series is stationary (mean reverting)"
            ),
        ]
        
        recommendation = "Price likely to revert to mean; position accordingly"
        
        return MarketSignal(
            signal_id=self._generate_signal_id(market),
            market=market,
            symbol=symbol,
            category=category,
            signal_type=SignalType.TREND_REVERSAL,
            confidence=confidence,
            score=confidence,
            indicators=indicators,
            recommendation=recommendation,
            created_at=datetime.now(timezone.utc),
            expires_at=None,
            metadata={
                "analyzer": "StatisticalTestsFramework",
                "test_results": test_results,
            }
        )
    
    def generate_signals(
        self,
        market: str,
        symbol: str,
        analysis_results: Dict,
        category: SignalCategory = SignalCategory.POLITICS,
    ) -> List[MarketSignal]:
        """
        Generate multiple signals from combined analysis results.
        
        Args:
            market: Market name
            symbol: Trading symbol
            analysis_results: Dict with results from all analyzers
            category: Market category
        
        Returns:
            List of MarketSignal objects
        """
        signals = []
        
        # Generate signal from spread analysis
        if "spread_metrics" in analysis_results:
            spread_signal = self.generate_spread_signal(
                market, symbol,
                analysis_results["spread_metrics"],
                category
            )
            if spread_signal:
                signals.append(spread_signal)
        
        # Generate signal from volume analysis
        if "volume_metrics" in analysis_results:
            volume_signal = self.generate_volume_signal(
                market, symbol,
                analysis_results["volume_metrics"],
                category
            )
            if volume_signal:
                signals.append(volume_signal)
        
        # Generate signal from statistical analysis
        if "test_results" in analysis_results:
            stat_signal = self.generate_statistical_signal(
                market, symbol,
                analysis_results["test_results"],
                category
            )
            if stat_signal:
                signals.append(stat_signal)
        
        logger.info(f"Generated {len(signals)} signals for {market}")
        return signals
    
    def rank_signals(self, signals: List[MarketSignal]) -> List[MarketSignal]:
        """
        Rank signals by confidence and score.
        
        Args:
            signals: List of market signals
        
        Returns:
            Sorted list (highest confidence first)
        """
        return sorted(
            signals,
            key=lambda s: (s.confidence, s.score),
            reverse=True
        )
    
    def filter_signals(
        self,
        signals: List[MarketSignal],
        min_confidence: float = 50.0,
        signal_types: Optional[List[SignalType]] = None
    ) -> List[MarketSignal]:
        """
        Filter signals by confidence and type.
        
        Args:
            signals: List of market signals
            min_confidence: Minimum confidence threshold
            signal_types: List of signal types to include
        
        Returns:
            Filtered list of signals
        """
        filtered = [s for s in signals if s.confidence >= min_confidence]
        
        if signal_types:
            filtered = [s for s in filtered if s.signal_type in signal_types]
        
        return filtered
