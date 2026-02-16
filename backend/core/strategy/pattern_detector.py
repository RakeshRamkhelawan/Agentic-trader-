from enum import Enum
from typing import List, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel


class SignalType(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class PatternName(str, Enum):
    SMA_CROSSOVER = "sma_crossover"
    BOLLINGER_BREAKOUT = "bollinger_breakout"
    RSI_OVERBOUGHT = "rsi_overbought"
    RSI_OVERSOLD = "rsi_oversold"
    DOJI = "doji"
    HAMMER = "hammer"
    ENGULFING = "engulfing"


class PatternSignal(BaseModel):
    pattern: PatternName
    signal: SignalType
    confidence: float
    timestamp: Optional[str] = None


class PatternDetector:
    """
    Analyzes OHLCV data to detect technical patterns.
    """

    def __init__(self):
        pass

    def analyze(self, df: pd.DataFrame) -> List[PatternSignal]:
        """
        Analyze DataFrame for patterns.
        df columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        signals = []

        if df.empty or len(df) < 20:
            return signals

        # Calculate indicators
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()
        df["std_20"] = df["close"].rolling(window=20).std()
        df["upper_band"] = df["sma_20"] + (df["std_20"] * 2)
        df["lower_band"] = df["sma_20"] - (df["std_20"] * 2)

        # Helper for change
        df["change"] = df["close"].diff()
        df["gain"] = df["change"].mask(df["change"] < 0, 0)
        df["loss"] = -df["change"].mask(df["change"] > 0, 0)

        # RSI (14)
        avg_gain = df["gain"].rolling(window=14).mean()
        avg_loss = df["loss"].rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # Check latest candle (or last 2 for patterns)
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        # 1. SMA Crossover (Golden Cross / Death Cross - approx on 20/50 for ease)
        if (
            prev_row["sma_20"] <= prev_row["sma_50"]
            and last_row["sma_20"] > last_row["sma_50"]
        ):
            signals.append(
                PatternSignal(
                    pattern=PatternName.SMA_CROSSOVER,
                    signal=SignalType.BULLISH,
                    confidence=0.8,
                )
            )
        elif (
            prev_row["sma_20"] >= prev_row["sma_50"]
            and last_row["sma_20"] < last_row["sma_50"]
        ):
            signals.append(
                PatternSignal(
                    pattern=PatternName.SMA_CROSSOVER,
                    signal=SignalType.BEARISH,
                    confidence=0.8,
                )
            )

        # 2. Bollinger Breakout
        if last_row["close"] > last_row["upper_band"]:
            signals.append(
                PatternSignal(
                    pattern=PatternName.BOLLINGER_BREAKOUT,
                    signal=SignalType.BULLISH,
                    confidence=0.7,
                )
            )  # Or Mean Reversion Bearish? Context matters. Let's say Trend Following for now.
        elif last_row["close"] < last_row["lower_band"]:
            signals.append(
                PatternSignal(
                    pattern=PatternName.BOLLINGER_BREAKOUT,
                    signal=SignalType.BEARISH,
                    confidence=0.7,
                )
            )

        # 3. RSI
        if last_row["rsi"] > 70:
            signals.append(
                PatternSignal(
                    pattern=PatternName.RSI_OVERBOUGHT,
                    signal=SignalType.BEARISH,
                    confidence=0.6,
                )
            )
        elif last_row["rsi"] < 30:
            signals.append(
                PatternSignal(
                    pattern=PatternName.RSI_OVERSOLD,
                    signal=SignalType.BULLISH,
                    confidence=0.6,
                )
            )

        # 4. Doji
        body = abs(last_row["close"] - last_row["open"])
        range_ = last_row["high"] - last_row["low"]
        if range_ > 0 and (body / range_) < 0.1:
            signals.append(
                PatternSignal(
                    pattern=PatternName.DOJI, signal=SignalType.NEUTRAL, confidence=0.5
                )
            )

        return signals
