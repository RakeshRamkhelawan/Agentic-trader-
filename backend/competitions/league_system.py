"""League system for tiered trading competitions."""

import uuid
from typing import Any

from .models.competitor import Competitor, CompetitorStats, LeagueTier
from .models.league import League, LeaguePromotion


class LeagueSystem:
    """
    Manages the league tier system for trading competitions.

    Tiers:
    - BRONZE: 0-1,000 points (Beginners)
    - SILVER: 1,000-10,000 points (Intermediate)
    - GOLD: 10,000-50,000 points (Advanced)
    - DIAMOND: 50,000+ points (Expert)
    """

    def __init__(self):
        self._competitors: dict[str, Competitor] = {}
        self._leagues: dict[LeagueTier, League] = {}
        self._promotions: list[LeaguePromotion] = []

        # Initialize leagues
        self._init_leagues()

    def _init_leagues(self) -> None:
        """Initialize default leagues."""
        self._leagues[LeagueTier.BRONZE] = League(
            tier=LeagueTier.BRONZE,
            name="Bronze League",
            description="Entry level for new traders",
            min_points=0,
            max_points=1000,
            promotion_threshold=1000,
            demotion_threshold=0,
        )

        self._leagues[LeagueTier.SILVER] = League(
            tier=LeagueTier.SILVER,
            name="Silver League",
            description="Intermediate traders with proven skills",
            min_points=1000,
            max_points=10000,
            promotion_threshold=10000,
            demotion_threshold=500,
        )

        self._leagues[LeagueTier.GOLD] = League(
            tier=LeagueTier.GOLD,
            name="Gold League",
            description="Advanced traders with consistent performance",
            min_points=10000,
            max_points=50000,
            promotion_threshold=50000,
            demotion_threshold=5000,
        )

        self._leagues[LeagueTier.DIAMOND] = League(
            tier=LeagueTier.DIAMOND,
            name="Diamond League",
            description="Elite traders - top 1%",
            min_points=50000,
            max_points=999999999,
            promotion_threshold=999999999,  # Can't promote from Diamond
            demotion_threshold=25000,
        )

    def register_competitor(self, name: str, email: str) -> Competitor:
        """Register a new competitor."""
        competitor_id = str(uuid.uuid4())

        competitor = Competitor(
            id=competitor_id,
            name=name,
            email=email,
            tier=LeagueTier.BRONZE,
            points=0,
            stats=CompetitorStats(),
        )

        self._competitors[competitor_id] = competitor
        self._leagues[LeagueTier.BRONZE].add_competitor(competitor_id)

        return competitor

    def get_competitor(self, competitor_id: str) -> Competitor | None:
        """Get competitor by ID."""
        return self._competitors.get(competitor_id)

    def get_competitor_by_email(self, email: str) -> Competitor | None:
        """Get competitor by email."""
        for competitor in self._competitors.values():
            if competitor.email == email:
                return competitor
        return None

    def update_competitor_performance(
        self,
        competitor_id: str,
        pnl: float,
        is_win: bool,
    ) -> dict[str, Any]:
        """Update competitor after trade and check for promotion."""
        competitor = self._competitors.get(competitor_id)
        if not competitor:
            return {"error": "Competitor not found"}

        # Update stats
        old_tier = competitor.tier
        competitor.update_stats(pnl, is_win)

        # Award points based on performance
        points_earned = self._calculate_points(pnl, is_win)
        competitor.add_points(points_earned)

        # Check for promotion/demotion
        promotion_result = self._check_tier_change(competitor)

        return {
            "competitor_id": competitor_id,
            "points_earned": points_earned,
            "total_points": competitor.points,
            "old_tier": old_tier.value,
            "new_tier": competitor.tier.value,
            "promoted": promotion_result.get("promoted", False),
            "demoted": promotion_result.get("demoted", False),
            "message": promotion_result.get("message", ""),
        }

    def _calculate_points(self, pnl: float, is_win: bool) -> int:
        """Calculate points earned from a trade."""
        base_points = 10 if is_win else 0
        pnl_multiplier = min(abs(pnl) / 100, 10)  # Cap at 10x

        points = int(base_points + pnl_multiplier)
        return max(1, points)  # Minimum 1 point

    def _check_tier_change(self, competitor: Competitor) -> dict[str, Any]:
        """Check if competitor should change tier."""
        current_league = self._leagues[competitor.tier]
        result = {"promoted": False, "demoted": False, "message": ""}

        # Check promotion
        if competitor.points >= current_league.promotion_threshold:
            next_tier = League.get_next_tier(competitor.tier)
            if next_tier:
                self._promote_competitor(competitor, next_tier)
                result["promoted"] = True
                result["message"] = f"Congratulations! Promoted to {next_tier.value.upper()}!"

        # Check demotion
        elif competitor.points <= current_league.demotion_threshold:
            prev_tier = League.get_previous_tier(competitor.tier)
            if prev_tier:
                self._demote_competitor(competitor, prev_tier)
                result["demoted"] = True
                result["message"] = (
                    f"Demoted to {prev_tier.value.upper()}. Keep trading to climb back!"
                )

        return result

    def _promote_competitor(
        self,
        competitor: Competitor,
        new_tier: LeagueTier,
    ) -> None:
        """Promote competitor to higher tier."""
        old_tier = competitor.tier

        # Remove from old league
        self._leagues[old_tier].remove_competitor(competitor.id)

        # Update competitor
        competitor.tier = new_tier

        # Add to new league
        self._leagues[new_tier].add_competitor(competitor.id)

        # Record promotion
        promotion = LeaguePromotion(
            competitor_id=competitor.id,
            from_tier=old_tier,
            to_tier=new_tier,
            reason="performance",
            pnl_at_promotion=competitor.stats.total_pnl,
            rank_at_promotion=competitor.rank,
        )
        self._promotions.append(promotion)

    def _demote_competitor(
        self,
        competitor: Competitor,
        new_tier: LeagueTier,
    ) -> None:
        """Demote competitor to lower tier."""
        old_tier = competitor.tier

        # Remove from old league
        self._leagues[old_tier].remove_competitor(competitor.id)

        # Update competitor
        competitor.tier = new_tier

        # Add to new league
        self._leagues[new_tier].add_competitor(competitor.id)

        # Record demotion (as negative promotion)
        promotion = LeaguePromotion(
            competitor_id=competitor.id,
            from_tier=old_tier,
            to_tier=new_tier,
            reason="performance",
            pnl_at_promotion=competitor.stats.total_pnl,
            rank_at_promotion=competitor.rank,
        )
        self._promotions.append(promotion)

    def get_league_standings(
        self,
        tier: LeagueTier,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get standings for a league."""
        league = self._leagues.get(tier)
        if not league:
            return []

        # Get competitors in this league
        competitors = [
            self._competitors[cid] for cid in league.competitor_ids if cid in self._competitors
        ]

        # Sort by points (descending)
        competitors.sort(key=lambda c: c.points, reverse=True)

        # Build standings
        standings = []
        for rank, competitor in enumerate(competitors[:limit], 1):
            competitor.rank = rank
            standings.append(
                {
                    "rank": rank,
                    "competitor_id": competitor.id,
                    "name": competitor.name,
                    "points": competitor.points,
                    "tier": competitor.tier.value,
                    "total_pnl": competitor.stats.total_pnl,
                    "win_rate": competitor.stats.win_rate,
                    "reputation": competitor.stats.reputation_score,
                }
            )

        return standings

    def get_all_leagues_info(self) -> dict[str, Any]:
        """Get information about all leagues."""
        return {
            tier.value: {
                **league.get_tier_requirements(),
                "best_performer": (
                    self._competitors.get(league.best_performer_id).name
                    if league.best_performer_id
                    else None
                ),
            }
            for tier, league in self._leagues.items()
        }

    def get_promotion_history(self, competitor_id: str) -> list[dict[str, Any]]:
        """Get promotion history for a competitor."""
        history = [
            {
                "from_tier": p.from_tier.value,
                "to_tier": p.to_tier.value,
                "timestamp": p.promoted_at.isoformat(),
                "reason": p.reason,
                "pnl_at_promotion": p.pnl_at_promotion,
            }
            for p in self._promotions
            if p.competitor_id == competitor_id
        ]
        return history
