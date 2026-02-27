"""Strategy sharing service for social trading."""

import uuid
from datetime import datetime
from typing import Any

from .models.competitor import Competitor
from .models.strategy import (
    SharedStrategy,
    StrategyFork,
    StrategyLanguage,
    StrategyMetrics,
    StrategyVisibility,
)


class StrategySharingService:
    """
    Manages strategy sharing, forking, and discovery.

    Features:
    - Share strategies publicly or within league
    - Fork and improve existing strategies
    - Rate and review strategies
    - Discover top-performing strategies
    """

    def __init__(self):
        self._strategies: dict[str, SharedStrategy] = {}
        self._author_strategies: dict[str, list[str]] = defaultdict(list)
        self._tag_index: dict[str, list[str]] = defaultdict(list)

    def share_strategy(
        self,
        author: Competitor,
        name: str,
        description: str,
        code: str,
        language: StrategyLanguage = StrategyLanguage.PYTHON,
        visibility: StrategyVisibility = StrategyVisibility.PUBLIC,
        tags: list[str] | None = None,
        metrics: StrategyMetrics | None = None,
    ) -> dict[str, Any]:
        """Share a new strategy."""
        strategy_id = str(uuid.uuid4())

        strategy = SharedStrategy(
            id=strategy_id,
            name=name,
            description=description,
            author_id=author.id,
            author_name=author.name,
            code=code,
            language=language,
            visibility=visibility,
            tags=tags or [],
            metrics=metrics or StrategyMetrics(),
        )

        self._strategies[strategy_id] = strategy
        self._author_strategies[author.id].append(strategy_id)

        # Index by tags
        for tag in strategy.tags:
            self._tag_index[tag.lower()].append(strategy_id)

        # Update author stats
        author.stats.strategies_shared += 1

        return {
            "success": True,
            "strategy_id": strategy_id,
            "author": author.name,
            "visibility": visibility.value,
        }

    def fork_strategy(
        self,
        original_strategy_id: str,
        forker: Competitor,
        modifications: str = "",
    ) -> dict[str, Any]:
        """Fork an existing strategy."""
        original = self._strategies.get(original_strategy_id)
        if not original:
            return {"error": "Strategy not found"}

        # Check visibility
        if original.visibility == StrategyVisibility.PRIVATE:
            if original.author_id != forker.id:
                return {"error": "Cannot fork private strategy"}

        # Create fork
        fork_id = str(uuid.uuid4())
        fork = StrategyFork(
            id=fork_id,
            original_strategy_id=original_strategy_id,
            forked_by=forker.id,
            modifications=modifications,
        )

        original.add_fork(fork)

        # Update forker stats
        forker.stats.strategies_forked += 1

        return {
            "success": True,
            "fork_id": fork_id,
            "original_strategy_id": original_strategy_id,
            "forked_by": forker.id,
        }

    def get_strategy(self, strategy_id: str) -> dict[str, Any] | None:
        """Get strategy details."""
        strategy = self._strategies.get(strategy_id)
        if not strategy:
            return None

        strategy.increment_views()
        return strategy.to_dict()

    def download_strategy(self, strategy_id: str) -> dict[str, Any] | None:
        """Download strategy code."""
        strategy = self._strategies.get(strategy_id)
        if not strategy:
            return None

        strategy.increment_downloads()

        return {
            "strategy_id": strategy_id,
            "name": strategy.name,
            "code": strategy.code,
            "language": strategy.language.value,
            "author": strategy.author_name,
            "license": "MIT",  # Default license
        }

    def like_strategy(self, strategy_id: str) -> dict[str, Any]:
        """Like a strategy."""
        strategy = self._strategies.get(strategy_id)
        if not strategy:
            return {"error": "Strategy not found"}

        strategy.increment_likes()

        return {
            "success": True,
            "strategy_id": strategy_id,
            "total_likes": strategy.likes,
        }

    def search_strategies(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        language: str | None = None,
        min_score: float = 0.0,
        sort_by: str = "score",
        limit: int = 20,
    ) -> dict[str, Any]:
        """Search for strategies."""
        results = list(self._strategies.values())

        # Filter by visibility (only public strategies in search)
        results = [s for s in results if s.visibility == StrategyVisibility.PUBLIC]

        # Filter by query (name/description)
        if query:
            query_lower = query.lower()
            results = [
                s for s in results
                if query_lower in s.name.lower() or query_lower in s.description.lower()
            ]

        # Filter by tags
        if tags:
            tag_set = set(t.lower() for t in tags)
            results = [
                s for s in results
                if tag_set & set(t.lower() for t in s.tags)
            ]

        # Filter by language
        if language:
            results = [s for s in results if s.language.value == language.lower()]

        # Filter by score
        results = [s for s in results if s.calculate_score() >= min_score]

        # Sort
        if sort_by == "score":
            results.sort(key=lambda s: s.calculate_score(), reverse=True)
        elif sort_by == "likes":
            results.sort(key=lambda s: s.likes, reverse=True)
        elif sort_by == "newest":
            results.sort(key=lambda s: s.created_at, reverse=True)
        elif sort_by == "downloads":
            results.sort(key=lambda s: s.downloads, reverse=True)

        # Paginate
        paginated = results[:limit]

        return {
            "strategies": [s.to_dict() for s in paginated],
            "total_results": len(results),
            "limit": limit,
        }

    def get_popular_strategies(self, limit: int = 10) -> dict[str, Any]:
        """Get most popular strategies."""
        # Sort by composite popularity score
        strategies = sorted(
            self._strategies.values(),
            key=lambda s: (s.likes * 2 + s.downloads * 3 + s.views * 0.1),
            reverse=True,
        )

        return {
            "strategies": [s.to_dict() for s in strategies[:limit]],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_top_performing_strategies(self, limit: int = 10) -> dict[str, Any]:
        """Get strategies with best performance metrics."""
        # Filter strategies with actual trades
        valid_strategies = [
            s for s in self._strategies.values()
            if s.metrics.total_trades > 5  # Minimum trades for validity
        ]

        # Sort by backtest score
        strategies = sorted(
            valid_strategies,
            key=lambda s: s.calculate_score(),
            reverse=True,
        )

        return {
            "strategies": [s.to_dict() for s in strategies[:limit]],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_author_strategies(self, author_id: str) -> dict[str, Any]:
        """Get all strategies by an author."""
        strategy_ids = self._author_strategies.get(author_id, [])
        strategies = [
            self._strategies[sid] for sid in strategy_ids
            if sid in self._strategies
        ]

        return {
            "author_id": author_id,
            "strategy_count": len(strategies),
            "strategies": [s.to_dict() for s in strategies],
        }

    def get_trending_tags(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get most popular strategy tags."""
        tag_counts = [
            {"tag": tag, "count": len(strategies)}
            for tag, strategies in self._tag_index.items()
        ]

        # Sort by count
        tag_counts.sort(key=lambda x: x["count"], reverse=True)

        return tag_counts[:limit]

    def get_strategy_analytics(self, strategy_id: str) -> dict[str, Any] | None:
        """Get detailed analytics for a strategy."""
        strategy = self._strategies.get(strategy_id)
        if not strategy:
            return None

        return {
            "strategy_id": strategy_id,
            "engagement": {
                "views": strategy.views,
                "likes": strategy.likes,
                "downloads": strategy.downloads,
                "forks": len(strategy.forks),
            },
            "performance": {
                "total_return": strategy.metrics.total_return,
                "sharpe_ratio": strategy.metrics.sharpe_ratio,
                "max_drawdown": strategy.metrics.max_drawdown,
                "win_rate": strategy.metrics.win_rate,
                "total_trades": strategy.metrics.total_trades,
            },
            "score": strategy.calculate_score(),
            "created_at": strategy.created_at.isoformat(),
            "updated_at": strategy.updated_at.isoformat(),
        }

    def update_strategy_metrics(
        self,
        strategy_id: str,
        metrics: StrategyMetrics,
    ) -> dict[str, Any]:
        """Update performance metrics for a strategy."""
        strategy = self._strategies.get(strategy_id)
        if not strategy:
            return {"error": "Strategy not found"}

        strategy.metrics = metrics
        strategy.updated_at = datetime.utcnow()

        return {
            "success": True,
            "strategy_id": strategy_id,
            "new_score": strategy.calculate_score(),
        }


from collections import defaultdict
