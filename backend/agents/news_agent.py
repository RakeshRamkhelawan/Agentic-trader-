"""
News Agent - Multi-source crypto news aggregation
Uses FREE APIs (no registration required):
- CryptoPanic (public endpoint, no key needed)
- CoinGecko (free tier, no key needed)
- Alternative.me Fear & Greed (no key needed)
- Reddit r/cryptocurrency (JSON API, no key needed)

Optional (requires API key):
- Finnhub (60 calls/min, sentiment scores)
- CryptoCompare (if key provided)
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import aiohttp

from backend.core.memory_agent import MemoryAgent
from backend.schemas.agent_messages import AgentMessage

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """Single news item with metadata."""

    title: str
    source: str
    url: str | None = None
    published_at: datetime | None = None
    sentiment_vote: int = 0  # For CryptoPanic: positive - negative votes
    currency: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "sentiment_vote": self.sentiment_vote,
            "currency": self.currency,
        }


class NewsAgent:
    """
    News Agent aggregates crypto news from multiple free sources.

    FREE Sources (no registration required):
    - CryptoPanic (public endpoint, community voting)
    - CoinGecko (free tier, coin updates)
    - Alternative.me Fear & Greed Index (market sentiment)
    - Reddit r/cryptocurrency (community discussions)

    Optional Sources (requires API key):
    - Finnhub (60 calls/min, sentiment scores)
    - CryptoCompare (if key provided)
    """

    def __init__(
        self,
        memory_agent: MemoryAgent | None = None,
        message_bus=None,
        cryptopanic_api_key: str | None = None,
        finnhub_api_key: str | None = None,
        cryptocompare_api_key: str | None = None,
        cache_ttl: int = 300,  # 5 minutes
        enable_reddit: bool = True,
        enable_fear_greed: bool = True,
    ):
        self.memory = memory_agent or MemoryAgent()
        self.message_bus = message_bus
        self.cryptopanic_api_key = cryptopanic_api_key
        self.finnhub_api_key = finnhub_api_key
        self.cryptocompare_api_key = cryptocompare_api_key
        self.enable_reddit = enable_reddit
        self.enable_fear_greed = enable_fear_greed
        self.cache_ttl = cache_ttl

        self._cache: dict[str, Any] = {}
        self._cache_time: dict[str, datetime] = {}

        self.name = "NewsAgent"
        self.prana = 50.0
        self.is_active = True
        self._fear_greed_value: int | None = None  # Cache fear & greed index

    async def fetch_coins(self, coins: list[str] = None) -> dict[str, list[NewsItem]]:
        """
        Fetch news for specified coins or general crypto news.

        Returns:
            Dict mapping coin symbol to list of NewsItems
        """
        if coins is None:
            coins = ["BTC", "ETH", "SOL", "XRP", "DOGE"]

        results = {}

        # Fetch from all sources concurrently
        tasks = []
        for coin in coins:
            tasks.append(self._fetch_coin_news(coin))

        fetched = await asyncio.gather(*tasks, return_exceptions=True)

        for coin, news_list in zip(coins, fetched, strict=False):
            if isinstance(news_list, Exception):
                logger.error(f"Error fetching news for {coin}: {news_list}")
                results[coin] = []
            else:
                results[coin] = news_list

        return results

    async def _fetch_coin_news(self, coin: str) -> list[NewsItem]:
        """Fetch news for a single coin from all sources."""
        all_news = []

        # Try CryptoPanic (FREE, no key needed)
        try:
            cp_news = await self._fetch_cryptopanic(coin)
            all_news.extend(cp_news)
        except Exception as e:
            logger.debug(f"CryptoPanic fetch failed for {coin}: {e}")

        # Try CoinGecko (FREE, no key needed)
        try:
            cg_news = await self._fetch_coingecko(coin)
            all_news.extend(cg_news)
        except Exception as e:
            logger.debug(f"CoinGecko fetch failed for {coin}: {e}")

        # Try Reddit r/cryptocurrency (FREE, no key needed)
        if self.enable_reddit:
            try:
                reddit_news = await self._fetch_reddit(coin)
                all_news.extend(reddit_news)
            except Exception as e:
                logger.debug(f"Reddit fetch failed for {coin}: {e}")

        # Try Fear & Greed Index (FREE, no key needed) - only for BTC as market indicator
        if self.enable_fear_greed and coin.upper() == "BTC":
            try:
                fear_greed_news = await self._fetch_fear_greed()
                all_news.extend(fear_greed_news)
            except Exception as e:
                logger.debug(f"Fear & Greed fetch failed: {e}")

        # Try Finnhub if key available (PAID - optional)
        if self.finnhub_api_key:
            try:
                fh_news = await self._fetch_finnhub(coin)
                all_news.extend(fh_news)
            except Exception as e:
                logger.debug(f"Finnhub fetch failed for {coin}: {e}")

        # Try CryptoCompare if key available (PAID - optional)
        if self.cryptocompare_api_key:
            try:
                cc_news = await self._fetch_cryptocompare(coin)
                all_news.extend(cc_news)
            except Exception as e:
                logger.debug(f"CryptoCompare fetch failed for {coin}: {e}")

        # Deduplicate by title hash
        seen = set()
        unique_news = []
        for item in all_news:
            title_hash = hashlib.md5(item.title.lower().encode()).hexdigest()[:16]
            if title_hash not in seen:
                seen.add(title_hash)
                unique_news.append(item)

        # Sort by recency (if available)
        unique_news.sort(
            key=lambda x: x.published_at or datetime.min.replace(tzinfo=UTC), reverse=True
        )

        return unique_news[:20]  # Return top 20

    async def _fetch_cryptopanic(self, coin: str) -> list[NewsItem]:
        """Fetch from CryptoPanic API."""
        url = "https://cryptopanic.com/api/v1/posts/"
        params = {
            "currencies": coin,
            "public": "true",
        }
        if self.cryptopanic_api_key:
            params["auth_token"] = self.cryptopanic_api_key

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    raise Exception(f"CryptoPanic returned {resp.status}")
                data = await resp.json()

        results = []
        for post in data.get("results", []):
            votes = post.get("votes", {})
            sentiment = votes.get("positive", 0) - votes.get("negative", 0)

            news_item = NewsItem(
                title=post.get("title", ""),
                source="cryptopanic",
                url=post.get("url"),
                published_at=(
                    datetime.fromisoformat(post.get("published_at").replace("Z", "+00:00"))
                    if post.get("published_at")
                    else None
                ),
                sentiment_vote=sentiment,
                currency=coin,
                metadata={
                    "domain": post.get("domain"),
                    "votes": votes,
                },
            )
            results.append(news_item)

        return results

    async def _fetch_coingecko(self, coin: str) -> list[NewsItem]:
        """Fetch from CoinGecko News API."""
        # CoinGecko uses coin IDs, map common symbols
        coin_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "XRP": "ripple",
            "DOGE": "dogecoin",
        }
        coin_id = coin_map.get(coin.upper(), coin.lower())

        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/status_updates"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 429:
                    raise Exception("CoinGecko rate limit exceeded")
                if resp.status != 200:
                    raise Exception(f"CoinGecko returned {resp.status}")
                data = await resp.json()

        results = []
        for update in data.get("status_updates", [])[:10]:
            news_item = NewsItem(
                title=update.get("description", ""),
                source="coingecko",
                url=update.get("user", {}).get("profile_url"),
                published_at=(
                    datetime.fromisoformat(update.get("created_at").replace("Z", "+00:00"))
                    if update.get("created_at")
                    else None
                ),
                currency=coin,
                metadata={
                    "user": update.get("user", {}).get("name"),
                },
            )
            results.append(news_item)

        return results

    async def _fetch_finnhub(self, coin: str) -> list[NewsItem]:
        """Fetch from Finnhub API."""
        url = "https://finnhub.io/api/v1/news"
        params = {
            "category": "crypto",
            "token": self.finnhub_api_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    raise Exception(f"Finnhub returned {resp.status}")
                data = await resp.json()

        results = []
        for article in data[:10]:  # Top 10
            # Check if article mentions our coin
            title = article.get("headline", "").lower()
            summary = article.get("summary", "").lower()
            coin_lower = coin.lower()

            if coin_lower not in title and coin_lower not in summary:
                continue

            news_item = NewsItem(
                title=article.get("headline", ""),
                source="finnhub",
                url=article.get("url"),
                published_at=(
                    datetime.fromtimestamp(article.get("datetime"))
                    if article.get("datetime")
                    else None
                ),
                sentiment_vote=int(
                    article.get("sentiment", 0) * 10
                ),  # Scale to roughly match CryptoPanic
                currency=coin,
                metadata={
                    "source": article.get("source"),
                },
            )
            results.append(news_item)

        return results

    async def _fetch_reddit(self, coin: str) -> list[NewsItem]:
        """
        Fetch from Reddit r/cryptocurrency JSON API (FREE, no key needed).
        Reddit's JSON API is publicly accessible without authentication.
        """
        # Map coins to search terms
        coin_terms = {
            "BTC": ["bitcoin", "btc"],
            "ETH": ["ethereum", "eth"],
            "SOL": ["solana", "sol"],
            "XRP": ["xrp", "ripple"],
            "DOGE": ["dogecoin", "doge"],
        }

        search_terms = coin_terms.get(coin.upper(), [coin.lower()])

        # Try hot posts from r/cryptocurrency
        urls = [
            "https://www.reddit.com/r/cryptocurrency/hot.json?limit=25",
            "https://www.reddit.com/r/CryptoMarkets/hot.json?limit=25",
        ]

        results = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        async with aiohttp.ClientSession(headers=headers) as session:
            for url in urls:
                try:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()

                        for post in data.get("data", {}).get("children", []):
                            post_data = post.get("data", {})
                            title = post_data.get("title", "").lower()

                            # Check if post mentions our coin
                            if not any(term in title for term in search_terms):
                                continue

                            # Calculate sentiment based on upvotes
                            ups = post_data.get("ups", 0)
                            downs = post_data.get("downs", 0)
                            sentiment = min(50, max(-50, (ups - downs) / 10))

                            # Create NewsItem
                            news_item = NewsItem(
                                title=post_data.get("title", ""),
                                source="reddit",
                                url=f"https://reddit.com{post_data.get('permalink', '')}",
                                published_at=(
                                    datetime.fromtimestamp(post_data.get("created_utc"), tz=UTC)
                                    if post_data.get("created_utc")
                                    else None
                                ),
                                sentiment_vote=int(sentiment),
                                currency=coin,
                                metadata={
                                    "subreddit": post_data.get("subreddit"),
                                    "upvotes": ups,
                                    "comment_count": post_data.get("num_comments"),
                                },
                            )
                            results.append(news_item)

                except Exception as e:
                    logger.debug(f"Reddit fetch from {url} failed: {e}")
                    continue

        return results[:10]  # Return top 10

    async def _fetch_fear_greed(self) -> list[NewsItem]:
        """
        Fetch Fear & Greed Index from Alternative.me (FREE, no key needed).
        This is a market sentiment indicator for the overall crypto market.
        """
        url = "https://api.alternative.me/fng/?limit=2"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    raise Exception(f"Fear & Greed API returned {resp.status}")
                data = await resp.json()

        results = []
        for item in data.get("data", []):
            try:
                value = int(item.get("value", 50))
                classification = item.get("value_classification", "Neutral")
                timestamp = int(item.get("timestamp", 0))

                # Convert to sentiment vote (-50 to +50 scale)
                # 0 = Extreme Fear, 50 = Neutral, 100 = Extreme Greed
                sentiment = value - 50  # -50 to +50

                # Create interpretive title
                if value < 20:
                    title = f"Market Fear & Greed: Extreme Fear ({value}) - Potential Buying Opportunity"
                elif value < 40:
                    title = f"Market Fear & Greed: Fear ({value}) - Caution Advised"
                elif value < 60:
                    title = f"Market Fear & Greed: Neutral ({value}) - Balanced Sentiment"
                elif value < 80:
                    title = f"Market Fear & Greed: Greed ({value}) - Consider Taking Profits"
                else:
                    title = (
                        f"Market Fear & Greed: Extreme Greed ({value}) - Market May Be Overheated"
                    )

                news_item = NewsItem(
                    title=title,
                    source="fear_greed",
                    url="https://alternative.me/crypto/fear-and-greed-index/",
                    published_at=(
                        datetime.fromtimestamp(timestamp, tz=UTC)
                        if timestamp
                        else datetime.now(UTC)
                    ),
                    sentiment_vote=sentiment,
                    currency="BTC",  # Market-wide indicator
                    metadata={
                        "index_value": value,
                        "classification": classification,
                        "type": "market_indicator",
                    },
                )
                results.append(news_item)
                self._fear_greed_value = value

            except Exception as e:
                logger.debug(f"Error parsing Fear & Greed item: {e}")
                continue

        return results

    async def _fetch_cryptocompare(self, coin: str) -> list[NewsItem]:
        """Fetch from CryptoCompare API (requires API key for news)."""
        if not self.cryptocompare_api_key:
            return []

        url = "https://min-api.cryptocompare.com/data/v2/news/"
        params = {
            "lang": "EN",
            "api_key": self.cryptocompare_api_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    raise Exception(f"CryptoCompare returned {resp.status}")
                data = await resp.json()

        results = []
        for article in data.get("Data", [])[:15]:
            title = article.get("title", "").lower()
            body = article.get("body", "").lower()
            coin_lower = coin.lower()

            # Check if article mentions our coin
            if coin_lower not in title and coin_lower not in body:
                continue

            # Simple sentiment based on categories
            sentiment = 0
            categories = article.get("categories", "").lower()
            if "bullish" in categories or "partnership" in categories:
                sentiment = 20
            elif "bearish" in categories or "hack" in categories:
                sentiment = -20

            news_item = NewsItem(
                title=article.get("title", ""),
                source="cryptocompare",
                url=article.get("url"),
                published_at=(
                    datetime.fromtimestamp(article.get("published_on"), tz=UTC)
                    if article.get("published_on")
                    else None
                ),
                sentiment_vote=sentiment,
                currency=coin,
                metadata={
                    "source": article.get("source"),
                    "categories": categories,
                },
            )
            results.append(news_item)

        return results

    def calculate_aggregated_sentiment(self, news_items: list[NewsItem]) -> dict[str, Any]:
        """
        Calculate aggregated sentiment from news items.

        Returns:
            Dict with score (0-1), trend (bullish/bearish/neutral), and metadata
        """
        if not news_items:
            return {"score": 0.5, "trend": "neutral", "confidence": 0.0, "sample_size": 0}

        # Calculate weighted sentiment
        total_votes = 0
        weighted_sum = 0

        for item in news_items:
            weight = 1.0
            # More recent = higher weight
            if item.published_at:
                age_hours = (datetime.now(UTC) - item.published_at).total_seconds() / 3600
                if age_hours < 1:
                    weight = 2.0
                elif age_hours < 6:
                    weight = 1.5
                elif age_hours < 24:
                    weight = 1.0
                else:
                    weight = 0.5

            weighted_sum += item.sentiment_vote * weight
            total_votes += weight

        # Normalize to 0-1 scale
        # Assuming sentiment_vote ranges from roughly -50 to +50
        if total_votes > 0:
            normalized = (weighted_sum / total_votes + 50) / 100
            normalized = max(0.0, min(1.0, normalized))
        else:
            normalized = 0.5

        # Determine trend
        if normalized > 0.6:
            trend = "bullish"
        elif normalized < 0.4:
            trend = "bearish"
        else:
            trend = "neutral"

        # Confidence based on sample size
        confidence = min(1.0, len(news_items) / 10)

        return {
            "score": round(normalized, 3),
            "trend": trend,
            "confidence": round(confidence, 3),
            "sample_size": len(news_items),
            "sources": list(set(item.source for item in news_items)),
        }

    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages."""
        if message.type in ["FETCH_NEWS", "FETCH_NEWS_REQUEST"]:
            coins = message.payload.get("coins", ["BTC"])
            news = await self.fetch_coins(coins)

            # Calculate sentiment for each coin
            sentiments = {}
            for coin, items in news.items():
                sentiments[coin] = self.calculate_aggregated_sentiment(items)

            # Store in memory
            self.memory.store_thought(
                agent_id=self.name,
                text=f"Fetched news for {', '.join(coins)}. Sentiments: {sentiments}",
                metadata={
                    "type": "news_fetch",
                    "coin_count": len(coins),
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )

            # Broadcast results
            if self.message_bus:
                await self.message_bus(
                    AgentMessage(
                        source=self.name,
                        target=message.source or "all",
                        type="NEWS_UPDATE",
                        payload={
                            "news": {k: [i.to_dict() for i in v[:5]] for k, v in news.items()},
                            "sentiments": sentiments,
                        },
                    )
                )

            return sentiments

        elif message.type == "TIMER_TICK_1MIN":
            # Periodic fetch for major coins
            await self.handle_message(
                AgentMessage(
                    source="system",
                    target=self.name,
                    type="FETCH_NEWS",
                    payload={"coins": ["BTC", "ETH"]},
                )
            )

    async def start(self):
        """Start the agent."""
        logger.info("NewsAgent started")
        self.is_active = True

    async def stop(self):
        """Stop the agent."""
        logger.info("NewsAgent stopped")
        self.is_active = False
