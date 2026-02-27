"""
External MCP Tools.

Third-party API integrations for:
- Sentiment analysis (news, social media)
- Macro economic data
- Market news
- Technical indicators

These tools require API keys and may have rate limits.
"""

import logging
import os
from typing import Any

import httpx
from mcp.server.fastmcp import Context

from backend.mcp_broker.resilience import circuit_breaker, retry

logger = logging.getLogger(__name__)

# API Keys from environment
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")


# ============================================================================
# Sentiment Analysis Tools
# ============================================================================

@circuit_breaker(failure_threshold=3, timeout_seconds=60)
@retry(max_attempts=2)
async def external__sentiment_analysis(
    symbol: str,
    source: str = "news",
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Analyze sentiment for a symbol from news or social media.

    Args:
        symbol: Asset symbol (e.g., "BTC", "AAPL")
        source: "news", "social", or "combined"
        ctx: MCP context

    Returns:
        Sentiment score (-1.0 to 1.0) and confidence
    """
    if ctx:
        ctx.info(f"Analyzing sentiment for {symbol} from {source}")

    # Try to fetch real news if API key available
    if NEWS_API_KEY and source in ("news", "combined"):
        try:
            sentiment = await _fetch_news_sentiment(symbol)
            if sentiment:
                return sentiment
        except Exception as e:
            logger.warning(f"News API failed, using fallback: {e}")

    # Try DeepSeek LLM for sentiment if available
    if DEEPSEEK_API_KEY:
        try:
            sentiment = await _llm_sentiment_analysis(symbol, source)
            if sentiment:
                return sentiment
        except Exception as e:
            logger.warning(f"LLM sentiment failed, using fallback: {e}")

    # Fallback: simulated sentiment based on symbol hash
    import hashlib
    hash_val = int(hashlib.blake2b(symbol.encode(), digest_size=8).hexdigest(), 16)
    sentiment_score = ((hash_val % 100) / 50) - 1.0  # -1.0 to 1.0

    return {
        "symbol": symbol,
        "sentiment_score": round(sentiment_score, 2),
        "confidence": 0.6,
        "source": "fallback",
        "trend": "bullish" if sentiment_score > 0.2 else "bearish" if sentiment_score < -0.2 else "neutral",
        "key_factors": ["market_momentum", "volume_trend"],
    }


async def _fetch_news_sentiment(symbol: str) -> dict[str, Any] | None:
    """Fetch sentiment from news API."""
    # This would integrate with NewsAPI, CryptoPanic, etc.
    # For now, return None to use fallback
    return None


async def _llm_sentiment_analysis(symbol: str, source: str) -> dict[str, Any] | None:
    """Use LLM for sentiment analysis."""
    if not DEEPSEEK_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a financial sentiment analyzer. Analyze the sentiment for the given symbol. Respond ONLY with a JSON object: {'score': float (-1.0 to 1.0), 'confidence': float (0.0 to 1.0), 'trend': 'bullish|bearish|neutral', 'key_factors': [list of strings]}"
                        },
                        {
                            "role": "user",
                            "content": f"Analyze sentiment for {symbol} based on recent market data and {source}"
                        }
                    ],
                    "temperature": 0.3,
                }
            )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # Parse JSON from content
                import json
                import re

                # Extract JSON from markdown if present
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)

                result = json.loads(content)
                result["symbol"] = symbol
                result["source"] = "llm"
                return result

    except Exception as e:
        logger.error(f"LLM sentiment error: {e}")

    return None


@circuit_breaker(failure_threshold=5, timeout_seconds=30)
async def external__social_sentiment(
    symbol: str,
    platform: str = "twitter",
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Get social media sentiment.

    Args:
        symbol: Asset symbol
        platform: "twitter", "reddit", "combined"
        ctx: MCP context

    Returns:
        Social sentiment metrics
    """
    if ctx:
        ctx.info(f"Fetching social sentiment for {symbol} from {platform}")

    # Placeholder implementation
    # In production, this would integrate with Twitter API, Reddit API, etc.

    return {
        "symbol": symbol,
        "platform": platform,
        "sentiment_score": 0.15,
        "confidence": 0.5,
        "volume_24h": 1250,
        "trending": False,
        "top_keywords": ["bullish", "accumulation", "support"],
    }


# ============================================================================
# Macro Economic Tools
# ============================================================================

@circuit_breaker(failure_threshold=3, timeout_seconds=30)
@retry(max_attempts=2)
async def external__macro_indicators(
    indicator: str = "all",
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Get macro economic indicators.

    Args:
        indicator: "all", "inflation", "rates", "employment", "gdp"
        ctx: MCP context

    Returns:
        Macro economic data
    """
    if ctx:
        ctx.info(f"Fetching macro indicators: {indicator}")

    # Try to fetch from Alpha Vantage
    if ALPHA_VANTAGE_API_KEY and ALPHA_VANTAGE_API_KEY != "demo":
        try:
            macro = await _fetch_alpha_vantage_macro(indicator)
            if macro:
                return macro
        except Exception as e:
            logger.warning(f"Alpha Vantage failed, using fallback: {e}")

    # Fallback data
    return {
        "inflation": {
            "cpi_yoy": 3.2,
            "ppi_yoy": 2.8,
            "trend": "decreasing",
        },
        "rates": {
            "fed_funds": 5.25,
            "ecb_main": 4.0,
            "trend": "stable",
        },
        "employment": {
            "unemployment_us": 3.8,
            "nonfarm_payrolls": 200000,
            "trend": "stable",
        },
        "gdp": {
            "us_growth_yoy": 2.5,
            "eu_growth_yoy": 1.8,
            "trend": "stable",
        },
        "timestamp": "2026-02-25T12:00:00Z",
        "source": "fallback",
    }


async def _fetch_alpha_vantage_macro(indicator: str) -> dict[str, Any] | None:
    """Fetch macro data from Alpha Vantage."""
    # This would call Alpha Vantage API
    # For now, return None to use fallback
    return None


@circuit_breaker(failure_threshold=3, timeout_seconds=30)
async def external__market_correlation(
    symbol: str,
    benchmark: str = "SPX",
    period: str = "1y",
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Calculate correlation with market benchmark.

    Args:
        symbol: Asset symbol
        benchmark: Benchmark index (SPX, BTC, etc.)
        period: Period for correlation (1m, 3m, 6m, 1y)
        ctx: MCP context

    Returns:
        Correlation metrics
    """
    if ctx:
        ctx.info(f"Calculating correlation: {symbol} vs {benchmark}")

    # Simulated correlation calculation
    # In production, fetch historical data and calculate Pearson correlation

    correlations = {
        "SPX": 0.65,
        "BTC": 0.45,
        "GOLD": -0.15,
        "USD": -0.35,
    }

    return {
        "symbol": symbol,
        "benchmark": benchmark,
        "correlation": correlations.get(benchmark, 0.5),
        "beta": correlations.get(benchmark, 0.5) * 1.2,
        "r_squared": correlations.get(benchmark, 0.5) ** 2,
        "period": period,
        "confidence": 0.75,
    }


# ============================================================================
# News Tools
# ============================================================================

@circuit_breaker(failure_threshold=3, timeout_seconds=30)
@retry(max_attempts=2)
async def external__market_news(
    symbol: str | None = None,
    category: str = "crypto",
    limit: int = 5,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Get latest market news.

    Args:
        symbol: Optional symbol filter
        category: "crypto", "stocks", "forex", "macro"
        limit: Number of news items
        ctx: MCP context

    Returns:
        News articles with sentiment
    """
    if ctx:
        ctx.info(f"Fetching news for {symbol or category}")

    # Try to fetch real news
    if NEWS_API_KEY:
        try:
            news = await _fetch_news_api(symbol, category, limit)
            if news:
                return news
        except Exception as e:
            logger.warning(f"News API failed, using fallback: {e}")

    # Fallback news
    return {
        "articles": [
            {
                "title": f"Market Update: {symbol or 'Crypto'} shows mixed signals",
                "summary": "Technical indicators suggest cautious optimism with strong support levels.",
                "sentiment": "neutral",
                "published_at": "2026-02-25T10:00:00Z",
                "source": "MarketWatch",
            },
            {
                "title": "Institutional interest continues to grow",
                "summary": "Major institutions are increasing allocation to digital assets.",
                "sentiment": "positive",
                "published_at": "2026-02-25T08:30:00Z",
                "source": "Bloomberg",
            },
        ],
        "symbol": symbol,
        "category": category,
        "source": "fallback",
    }


async def _fetch_news_api(symbol: str | None, category: str, limit: int) -> dict[str, Any] | None:
    """Fetch news from NewsAPI."""
    if not NEWS_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            query = symbol if symbol else category
            response = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "sortBy": "publishedAt",
                    "pageSize": limit,
                    "apiKey": NEWS_API_KEY,
                }
            )

            if response.status_code == 200:
                data = response.json()
                articles = []

                for article in data.get("articles", [])[:limit]:
                    articles.append({
                        "title": article.get("title"),
                        "summary": article.get("description"),
                        "url": article.get("url"),
                        "published_at": article.get("publishedAt"),
                        "source": article.get("source", {}).get("name"),
                        "sentiment": "neutral",  # Would analyze with NLP
                    })

                return {
                    "articles": articles,
                    "symbol": symbol,
                    "category": category,
                    "source": "newsapi",
                }

    except Exception as e:
        logger.error(f"News API error: {e}")

    return None


# ============================================================================
# Technical Analysis Tools
# ============================================================================

@circuit_breaker(failure_threshold=5, timeout_seconds=30)
async def external__technical_indicators(
    symbol: str,
    price_history: list[float],
    indicators: list[str] | None = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Calculate technical indicators.

    Args:
        symbol: Asset symbol
        price_history: List of prices (oldest first)
        indicators: List of indicators to calculate (rsi, macd, sma, ema, bb)
        ctx: MCP context

    Returns:
        Technical indicator values
    """
    if ctx:
        ctx.info(f"Calculating technical indicators for {symbol}")

    if not price_history or len(price_history) < 20:
        return {
            "symbol": symbol,
            "error": "Insufficient price history (need at least 20 data points)",
        }

    if indicators is None:
        indicators = ["rsi", "sma", "ema"]

    result = {"symbol": symbol, "indicators": {}}

    # Calculate RSI
    if "rsi" in indicators:
        result["indicators"]["rsi"] = _calculate_rsi(price_history)

    # Calculate SMA
    if "sma" in indicators:
        result["indicators"]["sma_20"] = _calculate_sma(price_history, 20)
        result["indicators"]["sma_50"] = _calculate_sma(price_history, 50) if len(price_history) >= 50 else None

    # Calculate EMA
    if "ema" in indicators:
        result["indicators"]["ema_12"] = _calculate_ema(price_history, 12)
        result["indicators"]["ema_26"] = _calculate_ema(price_history, 26)

    # Calculate MACD
    if "macd" in indicators:
        result["indicators"]["macd"] = _calculate_macd(price_history)

    # Calculate Bollinger Bands
    if "bb" in indicators:
        result["indicators"]["bollinger_bands"] = _calculate_bollinger_bands(price_history)

    # Overall signal
    result["overall_signal"] = _technical_signal(result["indicators"])

    return result


def _calculate_rsi(prices: list[float], period: int = 14) -> dict[str, Any]:
    """Calculate RSI."""
    if len(prices) < period + 1:
        return {"value": 50, "signal": "neutral"}

    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

    signal = "oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral"

    return {"value": round(rsi, 2), "signal": signal}


def _calculate_sma(prices: list[float], period: int) -> float | None:
    """Calculate Simple Moving Average."""
    if len(prices) < period:
        return None
    return round(sum(prices[-period:]) / period, 2)


def _calculate_ema(prices: list[float], period: int) -> float | None:
    """Calculate Exponential Moving Average."""
    if len(prices) < period:
        return None

    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period

    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema

    return round(ema, 2)


def _calculate_macd(prices: list[float]) -> dict[str, Any]:
    """Calculate MACD."""
    ema_12 = _calculate_ema(prices, 12)
    ema_26 = _calculate_ema(prices, 26)

    if ema_12 is None or ema_26 is None:
        return {"value": 0, "signal": "neutral"}

    macd_line = ema_12 - ema_26

    # Signal line (9-day EMA of MACD) - simplified
    signal_line = macd_line * 0.9  # Approximation

    histogram = macd_line - signal_line

    signal = "bullish" if macd_line > signal_line else "bearish"

    return {
        "macd": round(macd_line, 4),
        "signal": round(signal_line, 4),
        "histogram": round(histogram, 4),
        "trend": signal,
    }


def _calculate_bollinger_bands(prices: list[float], period: int = 20, std_dev: float = 2.0) -> dict[str, Any]:
    """Calculate Bollinger Bands."""
    if len(prices) < period:
        return {"upper": None, "middle": None, "lower": None}

    sma = sum(prices[-period:]) / period
    variance = sum((p - sma) ** 2 for p in prices[-period:]) / period
    std = variance ** 0.5

    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)

    current_price = prices[-1]
    position = (current_price - lower) / (upper - lower) if upper != lower else 0.5

    return {
        "upper": round(upper, 2),
        "middle": round(sma, 2),
        "lower": round(lower, 2),
        "position": round(position, 2),
        "signal": "upper_band" if position > 0.8 else "lower_band" if position < 0.2 else "middle",
    }


def _technical_signal(indicators: dict) -> str:
    """Generate overall technical signal."""
    signals = []

    if "rsi" in indicators:
        rsi = indicators["rsi"]
        if isinstance(rsi, dict):
            signals.append(1 if rsi.get("signal") == "oversold" else -1 if rsi.get("signal") == "overbought" else 0)

    if "macd" in indicators:
        macd = indicators["macd"]
        if isinstance(macd, dict):
            signals.append(1 if macd.get("trend") == "bullish" else -1)

    if "bollinger_bands" in indicators:
        bb = indicators["bollinger_bands"]
        if isinstance(bb, dict):
            signals.append(1 if bb.get("signal") == "lower_band" else -1 if bb.get("signal") == "upper_band" else 0)

    total = sum(signals)

    if total >= 2:
        return "strong_buy"
    elif total == 1:
        return "buy"
    elif total == 0:
        return "neutral"
    elif total == -1:
        return "sell"
    else:
        return "strong_sell"
