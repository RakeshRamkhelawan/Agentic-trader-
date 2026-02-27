"""Tournament engine for weekly competitions."""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .models.tournament import (
    Tournament,
    TournamentEntry,
    TournamentStatus,
    TournamentType,
    PrizeDistribution,
)
from .models.competitor import Competitor


class TournamentEngine:
    """
    Manages trading tournaments.
    
    Features:
    - Weekly tournaments starting every Monday
    - Automatic prize distribution
    - Real-time leaderboard updates
    - Multiple tournament types
    """
    
    def __init__(self):
        self._tournaments: Dict[str, Tournament] = {}
        self._entries: Dict[str, TournamentEntry] = {}
        self._competitor_entries: Dict[str, List[str]] = {}  # competitor_id -> entry_ids
    
    def create_tournament(
        self,
        name: str,
        description: str,
        tournament_type: TournamentType = TournamentType.WEEKLY,
        start_time: Optional[datetime] = None,
        duration_days: int = 7,
        starting_balance: float = 10000.0,
        max_participants: int = 100,
        tier_requirement: Optional[str] = None,
        entry_fee: int = 0,
    ) -> Tournament:
        """Create a new tournament."""
        tournament_id = str(uuid.uuid4())
        
        if start_time is None:
            # Default: next Monday
            start_time = self._get_next_monday()
        
        end_time = start_time + timedelta(days=duration_days)
        
        # Default prize distribution
        prizes = [
            PrizeDistribution(position=1, points=1000, badge="gold_trophy", title="Champion"),
            PrizeDistribution(position=2, points=500, badge="silver_trophy", title="Runner-up"),
            PrizeDistribution(position=3, points=250, badge="bronze_trophy", title="Third Place"),
            PrizeDistribution(position=4, points=100),
            PrizeDistribution(position=5, points=100),
            PrizeDistribution(position=6, points=50),
            PrizeDistribution(position=7, points=50),
            PrizeDistribution(position=8, points=50),
            PrizeDistribution(position=9, points=50),
            PrizeDistribution(position=10, points=50),
        ]
        
        tournament = Tournament(
            id=tournament_id,
            name=name,
            description=description,
            type=tournament_type,
            status=TournamentStatus.PENDING,
            tier_requirement=tier_requirement,
            starting_balance=starting_balance,
            max_participants=max_participants,
            entry_fee_points=entry_fee,
            start_time=start_time,
            end_time=end_time,
            prizes=prizes,
        )
        
        self._tournaments[tournament_id] = tournament
        return tournament
    
    def _get_next_monday(self) -> datetime:
        """Get datetime for next Monday at 00:00 UTC."""
        now = datetime.utcnow()
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7  # Next Monday, not today
        
        next_monday = now + timedelta(days=days_until_monday)
        return next_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def enter_tournament(
        self,
        tournament_id: str,
        competitor: Competitor,
    ) -> Dict[str, Any]:
        """Enter a competitor into a tournament."""
        tournament = self._tournaments.get(tournament_id)
        if not tournament:
            return {"success": False, "error": "Tournament not found"}
        
        # Check if can enter
        if not tournament.can_enter(competitor.tier.value):
            return {
                "success": False,
                "error": f"Cannot enter tournament. Status: {tournament.status.value}",
            }
        
        # Check if already entered
        for entry in tournament.entries:
            if entry.competitor_id == competitor.id:
                return {"success": False, "error": "Already entered this tournament"}
        
        # Check entry fee
        if tournament.entry_fee_points > competitor.points:
            return {
                "success": False,
                "error": f"Insufficient points. Need {tournament.entry_fee_points}",
            }
        
        # Deduct entry fee
        competitor.points -= tournament.entry_fee_points
        
        # Create entry
        entry_id = str(uuid.uuid4())
        entry = TournamentEntry(
            competitor_id=competitor.id,
            tournament_id=tournament_id,
            starting_balance=tournament.starting_balance,
            current_balance=tournament.starting_balance,
        )
        
        # Store entry
        self._entries[entry_id] = entry
        tournament.add_entry(entry)
        
        # Track competitor's entries
        if competitor.id not in self._competitor_entries:
            self._competitor_entries[competitor.id] = []
        self._competitor_entries[competitor.id].append(entry_id)
        
        competitor.stats.competitions_entered += 1
        
        return {
            "success": True,
            "entry_id": entry_id,
            "tournament_id": tournament_id,
            "starting_balance": tournament.starting_balance,
        }
    
    def update_entry_balance(
        self,
        tournament_id: str,
        competitor_id: str,
        new_balance: float,
    ) -> Dict[str, Any]:
        """Update a competitor's balance in a tournament."""
        tournament = self._tournaments.get(tournament_id)
        if not tournament:
            return {"error": "Tournament not found"}
        
        if not tournament.is_active():
            return {"error": "Tournament is not active"}
        
        # Find entry
        entry = None
        for e in tournament.entries:
            if e.competitor_id == competitor_id:
                entry = e
                break
        
        if not entry:
            return {"error": "Not entered in this tournament"}
        
        entry.update_pnl(new_balance)
        entry.record_trade()
        
        return {
            "success": True,
            "new_balance": new_balance,
            "pnl": entry.pnl,
            "pnl_percentage": entry.pnl_percentage,
            "rank": entry.rank,
        }
    
    def get_leaderboard(
        self,
        tournament_id: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Get tournament leaderboard."""
        tournament = self._tournaments.get(tournament_id)
        if not tournament:
            return {"error": "Tournament not found"}
        
        tournament.update_rankings()
        top_entries = tournament.get_leaderboard(limit)
        
        return {
            "tournament_id": tournament_id,
            "tournament_name": tournament.name,
            "status": tournament.status.value,
            "total_participants": len(tournament.entries),
            "leaderboard": [
                {
                    "rank": entry.rank,
                    "competitor_id": entry.competitor_id,
                    "balance": entry.current_balance,
                    "pnl": entry.pnl,
                    "pnl_percentage": entry.pnl_percentage,
                    "trades": entry.trades_count,
                    "prize": tournament.get_prize_for_position(entry.rank),
                }
                for entry in top_entries
            ],
        }
    
    def start_tournament(self, tournament_id: str) -> Dict[str, Any]:
        """Start a pending tournament."""
        tournament = self._tournaments.get(tournament_id)
        if not tournament:
            return {"error": "Tournament not found"}
        
        if tournament.status != TournamentStatus.PENDING:
            return {"error": f"Tournament is {tournament.status.value}"}
        
        tournament.status = TournamentStatus.ACTIVE
        
        return {
            "success": True,
            "tournament_id": tournament_id,
            "participants": len(tournament.entries),
            "started_at": datetime.utcnow().isoformat(),
        }
    
    def end_tournament(self, tournament_id: str) -> Dict[str, Any]:
        """End a tournament and distribute prizes."""
        tournament = self._tournaments.get(tournament_id)
        if not tournament:
            return {"error": "Tournament not found"}
        
        if tournament.status != TournamentStatus.ACTIVE:
            return {"error": f"Tournament is {tournament.status.value}"}
        
        tournament.status = TournamentStatus.ENDED
        tournament.update_rankings()
        
        # Distribute prizes
        winners = []
        for entry in tournament.entries[:10]:  # Top 10
            prize = tournament.get_prize_for_position(entry.rank)
            if prize:
                winners.append({
                    "rank": entry.rank,
                    "competitor_id": entry.competitor_id,
                    "points_awarded": prize.points,
                    "badge": prize.badge,
                    "title": prize.title,
                })
        
        return {
            "success": True,
            "tournament_id": tournament_id,
            "ended_at": datetime.utcnow().isoformat(),
            "winners": winners,
        }
    
    def get_active_tournaments(self) -> List[Dict[str, Any]]:
        """Get all currently active tournaments."""
        active = []
        for tournament in self._tournaments.values():
            if tournament.is_active():
                active.append({
                    "id": tournament.id,
                    "name": tournament.name,
                    "type": tournament.type.value,
                    "participants": len(tournament.entries),
                    "max_participants": tournament.max_participants,
                    "ends_at": tournament.end_time.isoformat(),
                    "time_remaining": str(tournament.end_time - datetime.utcnow()),
                })
        return active
    
    def get_upcoming_tournaments(self) -> List[Dict[str, Any]]:
        """Get upcoming tournaments."""
        upcoming = []
        for tournament in self._tournaments.values():
            if tournament.status == TournamentStatus.PENDING:
                upcoming.append({
                    "id": tournament.id,
                    "name": tournament.name,
                    "type": tournament.type.value,
                    "starts_at": tournament.start_time.isoformat(),
                    "tier_requirement": tournament.tier_requirement,
                    "entry_fee": tournament.entry_fee_points,
                })
        return upcoming
    
    def get_competitor_tournaments(self, competitor_id: str) -> List[Dict[str, Any]]:
        """Get all tournaments a competitor has entered."""
        entry_ids = self._competitor_entries.get(competitor_id, [])
        tournaments = []
        
        for entry_id in entry_ids:
            entry = self._entries.get(entry_id)
            if entry:
                tournament = self._tournaments.get(entry.tournament_id)
                if tournament:
                    tournaments.append({
                        "tournament_id": tournament.id,
                        "tournament_name": tournament.name,
                        "status": tournament.status.value,
                        "rank": entry.rank,
                        "pnl": entry.pnl,
                        "pnl_percentage": entry.pnl_percentage,
                        "trades": entry.trades_count,
                    })
        
        return tournaments
    
    def create_weekly_tournament(self, week_number: int) -> Tournament:
        """Create a standard weekly tournament."""
        return self.create_tournament(
            name=f"Weekly Tournament #{week_number}",
            description=f"Weekly trading competition - Week {week_number}",
            tournament_type=TournamentType.WEEKLY,
            starting_balance=10000.0,
            max_participants=100,
            duration_days=7,
        )
