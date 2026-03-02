"""Strategy sharing models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class StrategyVisibility(Enum):
    """Strategy visibility levels."""
    PRIVATE = "private"
    PUBLIC = "public"
    LEAGUE_ONLY = "league_only"


class StrategyLanguage(Enum):
    """Strategy implementation language."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    PSEUDOCODE = "pseudocode"


@dataclass
class StrategyMetrics:
    """Performance metrics for a strategy."""
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    avg_trade_duration: float = 0.0
    backtest_score: float = 0.0


@dataclass
class StrategyFork:
    """A fork of a strategy."""
    id: str
    original_strategy_id: str
    forked_by: str
    forked_at: datetime = field(default_factory=datetime.utcnow)
    modifications: str = ""  # Description of changes
    improved_performance: float | None = None  # % improvement


@dataclass
class SharedStrategy:
    """A shared trading strategy."""
    id: str
    name: str
    description: str
    author_id: str
    author_name: str

    # Strategy details
    code: str
    language: StrategyLanguage
    visibility: StrategyVisibility = StrategyVisibility.PUBLIC
    tags: list[str] = field(default_factory=list)

    # Performance
    metrics: StrategyMetrics = field(default_factory=StrategyMetrics)

    # Engagement
    forks: list[StrategyFork] = field(default_factory=list)
    likes: int = 0
    views: int = 0
    downloads: int = 0

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

    def add_fork(self, fork: StrategyFork) -> None:
        """Add a fork to this strategy."""
        self.forks.append(fork)

    def increment_views(self) -> None:
        """Increment view count."""
        self.views += 1

    def increment_likes(self) -> None:
        """Increment like count."""
        self.likes += 1

    def increment_downloads(self) -> None:
        """Increment download count."""
        self.downloads += 1

    def calculate_score(self) -> float:
        """Calculate overall strategy score."""
        # Weighted scoring
        score = (
            self.metrics.total_return * 0.3 +
            self.metrics.sharpe_ratio * 20 * 0.25 +
            (100 - abs(self.metrics.max_drawdown)) * 0.2 +
            self.metrics.win_rate * 0.15 +
            min(self.likes * 0.5, 10) * 0.1  # Cap likes contribution
        )
        return max(0, score)  # Ensure non-negative

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "language": self.language.value,
            "visibility": self.visibility.value,
            "tags": self.tags,
            "metrics": {
                "total_return": self.metrics.total_return,
                "sharpe_ratio": self.metrics.sharpe_ratio,
                "max_drawdown": self.metrics.max_drawdown,
                "win_rate": self.metrics.win_rate,
                "profit_factor": self.metrics.profit_factor,
                "total_trades": self.metrics.total_trades,
            },
            "engagement": {
                "likes": self.likes,
                "views": self.views,
                "downloads": self.downloads,
                "forks": len(self.forks),
            },
            "score": self.calculate_score(),
            "created_at": self.created_at.isoformat(),
        }
