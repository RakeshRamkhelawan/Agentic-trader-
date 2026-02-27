"""Leaderboard service for real-time rankings."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

from .models.competitor import Competitor, LeagueTier


class LeaderboardService:
    """
    Manages real-time leaderboards across multiple dimensions.
    
    Leaderboards:
    - Global: All competitors ranked by points
    - League-specific: Within each tier
    - Weekly: Best performers this week
    - Monthly: Best performers this month
    - All-time: Historical rankings
    """
    
    def __init__(self):
        self._competitors: Dict[str, Competitor] = {}
        self._weekly_scores: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._monthly_scores: Dict[str, Dict[str, float]] = defaultdict(dict)
    
    def register_competitor(self, competitor: Competitor) -> None:
        """Register a competitor for leaderboard tracking."""
        self._competitors[competitor.id] = competitor
    
    def get_global_leaderboard(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get global leaderboard."""
        # Sort by points (descending)
        sorted_competitors = sorted(
            self._competitors.values(),
            key=lambda c: c.points,
            reverse=True,
        )
        
        # Apply pagination
        paginated = sorted_competitors[offset:offset + limit]
        
        # Build leaderboard
        leaderboard = []
        for rank, competitor in enumerate(paginated, offset + 1):
            leaderboard.append({
                "rank": rank,
                "competitor_id": competitor.id,
                "name": competitor.name,
                "tier": competitor.tier.value,
                "points": competitor.points,
                "total_pnl": round(competitor.stats.total_pnl, 2),
                "win_rate": round(competitor.stats.win_rate, 2),
                "sharpe_ratio": round(competitor.stats.sharpe_ratio, 2),
                "competitions_won": competitor.stats.competitions_won,
                "reputation": round(competitor.stats.reputation_score, 2),
            })
        
        return {
            "leaderboard": leaderboard,
            "total_count": len(sorted_competitors),
            "limit": limit,
            "offset": offset,
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def get_league_leaderboard(
        self,
        tier: LeagueTier,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Get leaderboard for a specific league tier."""
        # Filter by tier
        tier_competitors = [
            c for c in self._competitors.values()
            if c.tier == tier
        ]
        
        # Sort by points
        sorted_competitors = sorted(
            tier_competitors,
            key=lambda c: c.points,
            reverse=True,
        )
        
        # Build leaderboard
        leaderboard = []
        for rank, competitor in enumerate(sorted_competitors[:limit], 1):
            leaderboard.append({
                "rank": rank,
                "competitor_id": competitor.id,
                "name": competitor.name,
                "points": competitor.points,
                "total_pnl": round(competitor.stats.total_pnl, 2),
                "win_rate": round(competitor.stats.win_rate, 2),
                "reputation": round(competitor.stats.reputation_score, 2),
            })
        
        return {
            "tier": tier.value,
            "tier_name": tier.value.upper(),
            "leaderboard": leaderboard,
            "total_in_tier": len(tier_competitors),
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def get_weekly_leaderboard(self, limit: int = 20) -> Dict[str, Any]:
        """Get weekly performance leaderboard."""
        week_key = self._get_current_week_key()
        weekly_scores = self._weekly_scores.get(week_key, {})
        
        # Sort by weekly score
        sorted_scores = sorted(
            weekly_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        leaderboard = []
        for rank, (competitor_id, score) in enumerate(sorted_scores[:limit], 1):
            competitor = self._competitors.get(competitor_id)
            if competitor:
                leaderboard.append({
                    "rank": rank,
                    "competitor_id": competitor_id,
                    "name": competitor.name,
                    "tier": competitor.tier.value,
                    "weekly_score": round(score, 2),
                    "total_pnl": round(competitor.stats.total_pnl, 2),
                })
        
        return {
            "week": week_key,
            "leaderboard": leaderboard,
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def get_monthly_leaderboard(self, limit: int = 20) -> Dict[str, Any]:
        """Get monthly performance leaderboard."""
        month_key = self._get_current_month_key()
        monthly_scores = self._monthly_scores.get(month_key, {})
        
        # Sort by monthly score
        sorted_scores = sorted(
            monthly_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        leaderboard = []
        for rank, (competitor_id, score) in enumerate(sorted_scores[:limit], 1):
            competitor = self._competitors.get(competitor_id)
            if competitor:
                leaderboard.append({
                    "rank": rank,
                    "competitor_id": competitor_id,
                    "name": competitor.name,
                    "tier": competitor.tier.value,
                    "monthly_score": round(score, 2),
                    "total_pnl": round(competitor.stats.total_pnl, 2),
                })
        
        return {
            "month": month_key,
            "leaderboard": leaderboard,
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def get_competitor_rank(self, competitor_id: str) -> Optional[Dict[str, Any]]:
        """Get ranking information for a specific competitor."""
        competitor = self._competitors.get(competitor_id)
        if not competitor:
            return None
        
        # Calculate global rank
        all_competitors = sorted(
            self._competitors.values(),
            key=lambda c: c.points,
            reverse=True,
        )
        
        global_rank = next(
            (i + 1 for i, c in enumerate(all_competitors) if c.id == competitor_id),
            None,
        )
        
        # Calculate tier rank
        tier_competitors = sorted(
            [c for c in self._competitors.values() if c.tier == competitor.tier],
            key=lambda c: c.points,
            reverse=True,
        )
        
        tier_rank = next(
            (i + 1 for i, c in enumerate(tier_competitors) if c.id == competitor_id),
            None,
        )
        
        # Percentiles
        total_competitors = len(all_competitors)
        global_percentile = (1 - (global_rank / total_competitors)) * 100 if total_competitors > 0 else 0
        
        return {
            "competitor_id": competitor_id,
            "name": competitor.name,
            "global_rank": global_rank,
            "global_percentile": round(global_percentile, 1),
            "tier_rank": tier_rank,
            "tier": competitor.tier.value,
            "points": competitor.points,
            "total_competitors": total_competitors,
        }
    
    def update_weekly_score(self, competitor_id: str, score: float) -> None:
        """Update weekly score for a competitor."""
        week_key = self._get_current_week_key()
        self._weekly_scores[week_key][competitor_id] = score
    
    def update_monthly_score(self, competitor_id: str, score: float) -> None:
        """Update monthly score for a competitor."""
        month_key = self._get_current_month_key()
        self._monthly_scores[month_key][competitor_id] = score
    
    def _get_current_week_key(self) -> str:
        """Get current week identifier (YYYY-WW)."""
        now = datetime.utcnow()
        return f"{now.year}-W{now.isocalendar()[1]:02d}"
    
    def _get_current_month_key(self) -> str:
        """Get current month identifier (YYYY-MM)."""
        now = datetime.utcnow()
        return f"{now.year}-{now.month:02d}"
    
    def get_leaderboard_summary(self) -> Dict[str, Any]:
        """Get summary of all leaderboards."""
        return {
            "global": {
                "total_competitors": len(self._competitors),
                "top_performer": self._get_top_performer(),
            },
            "by_tier": {
                tier.value: len([c for c in self._competitors.values() if c.tier == tier])
                for tier in LeagueTier
            },
            "weekly": {
                "week": self._get_current_week_key(),
                "participants": len(self._weekly_scores.get(self._get_current_week_key(), {})),
            },
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def _get_top_performer(self) -> Optional[Dict[str, Any]]:
        """Get current top performer."""
        if not self._competitors:
            return None
        
        top = max(self._competitors.values(), key=lambda c: c.points)
        return {
            "competitor_id": top.id,
            "name": top.name,
            "points": top.points,
            "tier": top.tier.value,
        }
    
    def get_rising_stars(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get competitors with biggest rank improvements."""
        # This would require historical data
        # Simplified: return newest high-performers
        recent_high_performers = [
            c for c in self._competitors.values()
            if c.points > 500 and c.stats.total_trades > 10
        ]
        
        # Sort by reputation growth (simplified)
        sorted_performers = sorted(
            recent_high_performers,
            key=lambda c: c.stats.reputation_score,
            reverse=True,
        )
        
        return [
            {
                "competitor_id": c.id,
                "name": c.name,
                "tier": c.tier.value,
                "points": c.points,
                "reputation": round(c.stats.reputation_score, 2),
            }
            for c in sorted_performers[:limit]
        ]
