"""Tournament scheduler for automatic tournament management."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from backend.competitions.advanced_tournaments import (
    AdvancedTournamentEngine,
    TournamentVariant,
)


class ScheduleFrequency(Enum):
    """Tournament schedule frequencies."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class ScheduledTournament:
    """Scheduled tournament configuration."""

    id: str
    name_template: str
    description: str
    frequency: ScheduleFrequency
    variant: TournamentVariant | None = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    duration_hours: int = 168  # 1 week default
    max_participants: int = 100
    auto_start: bool = True
    auto_end: bool = True
    enabled: bool = True

    def generate_name(self, occurrence: int) -> str:
        """Generate tournament name for occurrence."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return self.name_template.format(
            date=date_str,
            occurrence=occurrence,
            week=datetime.utcnow().isocalendar()[1],
        )


class TournamentScheduler:
    """
    Manages scheduled tournament creation and lifecycle.

    Automatically creates tournaments based on schedules:
    - Weekly tournaments (every Monday)
    - Daily tournaments (every day)
    - Special event tournaments (scheduled dates)
    """

    def __init__(self):
        self._engine = AdvancedTournamentEngine()
        self._schedules: dict[str, ScheduledTournament] = {}
        self._active_tournaments: dict[str, str] = {}  # schedule_id -> tournament_id
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._callbacks: dict[str, list[Callable]] = {
            "on_create": [],
            "on_start": [],
            "on_end": [],
        }

    def add_schedule(self, schedule: ScheduledTournament) -> None:
        """Add a tournament schedule."""
        self._schedules[schedule.id] = schedule

    def remove_schedule(self, schedule_id: str) -> bool:
        """Remove a tournament schedule."""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            return True
        return False

    def enable_schedule(self, schedule_id: str) -> bool:
        """Enable a schedule."""
        if schedule_id in self._schedules:
            self._schedules[schedule_id].enabled = True
            return True
        return False

    def disable_schedule(self, schedule_id: str) -> bool:
        """Disable a schedule."""
        if schedule_id in self._schedules:
            self._schedules[schedule_id].enabled = False
            return True
        return False

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for tournament events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    async def _trigger_callback(self, event: str, data: Any) -> None:
        """Trigger callbacks for event."""
        for callback in self._callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception:
                pass  # Log error but continue

    async def create_tournament_from_schedule(
        self,
        schedule: ScheduledTournament,
        occurrence: int = 1,
    ) -> Any | None:
        """Create a tournament from schedule."""
        if not schedule.enabled:
            return None

        name = schedule.generate_name(occurrence)

        if schedule.variant:
            tournament = self._engine.create_variant_tournament(
                name=name,
                description=schedule.description,
                variant=schedule.variant,
                max_participants=schedule.max_participants,
                duration_days=schedule.duration_hours // 24,
            )
        else:
            tournament = self._engine.create_tournament(
                name=name,
                description=schedule.description,
                max_participants=schedule.max_participants,
                duration_days=schedule.duration_hours // 24,
            )

        # Store mapping
        self._active_tournaments[schedule.id] = tournament.id

        # Trigger callback
        await self._trigger_callback(
            "on_create",
            {
                "schedule_id": schedule.id,
                "tournament_id": tournament.id,
                "name": name,
            },
        )

        # Auto-start if configured
        if schedule.auto_start:
            self._engine.start_tournament(tournament.id)
            await self._trigger_callback(
                "on_start",
                {
                    "schedule_id": schedule.id,
                    "tournament_id": tournament.id,
                },
            )

        return tournament

    async def run_schedule_loop(self) -> None:
        """Main scheduling loop."""
        self._running = True

        while self._running:
            now = datetime.utcnow()

            for schedule in self._schedules.values():
                if not schedule.enabled:
                    continue

                # Check if tournament should be created
                if schedule.frequency == ScheduleFrequency.WEEKLY:
                    await self._handle_weekly_schedule(schedule, now)
                elif schedule.frequency == ScheduleFrequency.DAILY:
                    await self._handle_daily_schedule(schedule, now)
                elif schedule.frequency == ScheduleFrequency.HOURLY:
                    await self._handle_hourly_schedule(schedule, now)

            # Check for tournaments that should end
            await self._check_tournament_endings()

            # Sleep for 1 minute
            await asyncio.sleep(60)

    async def _handle_weekly_schedule(
        self,
        schedule: ScheduledTournament,
        now: datetime,
    ) -> None:
        """Handle weekly schedule - create on Monday 00:00."""
        # Check if it's Monday at midnight (within first 5 minutes)
        if now.weekday() == 0 and now.hour == 0 and now.minute < 5:
            # Check if we already created one this week
            week_key = f"{schedule.id}:{now.isocalendar()[1]}"
            if week_key not in self._active_tournaments:
                tournament = await self.create_tournament_from_schedule(
                    schedule,
                    occurrence=now.isocalendar()[1],
                )
                if tournament:
                    self._active_tournaments[week_key] = tournament.id

    async def _handle_daily_schedule(
        self,
        schedule: ScheduledTournament,
        now: datetime,
    ) -> None:
        """Handle daily schedule - create at midnight."""
        # Check if it's midnight (within first 5 minutes)
        if now.hour == 0 and now.minute < 5:
            day_key = f"{schedule.id}:{now.strftime('%Y%m%d')}"
            if day_key not in self._active_tournaments:
                tournament = await self.create_tournament_from_schedule(
                    schedule,
                    occurrence=now.timetuple().tm_yday,
                )
                if tournament:
                    self._active_tournaments[day_key] = tournament.id

    async def _handle_hourly_schedule(
        self,
        schedule: ScheduledTournament,
        now: datetime,
    ) -> None:
        """Handle hourly schedule."""
        # Create at the start of each hour
        if now.minute < 5:
            hour_key = f"{schedule.id}:{now.strftime('%Y%m%d%H')}"
            if hour_key not in self._active_tournaments:
                tournament = await self.create_tournament_from_schedule(
                    schedule,
                    occurrence=now.hour,
                )
                if tournament:
                    self._active_tournaments[hour_key] = tournament.id

    async def _check_tournament_endings(self) -> None:
        """Check for tournaments that should end."""
        # This would check actual tournament end times
        # For now, simplified implementation
        pass

    def start(self) -> None:
        """Start the scheduler."""
        if not self._running:
            task = asyncio.create_task(self.run_schedule_loop())
            self._tasks.append(task)

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()

    def get_status(self) -> dict[str, Any]:
        """Get scheduler status."""
        return {
            "running": self._running,
            "schedules_count": len(self._schedules),
            "active_tournaments": len(self._active_tournaments),
            "schedules": [
                {
                    "id": s.id,
                    "name_template": s.name_template,
                    "frequency": s.frequency.value,
                    "enabled": s.enabled,
                }
                for s in self._schedules.values()
            ],
        }

    def create_default_schedules(self) -> None:
        """Create default tournament schedules."""
        # Weekly main tournament
        self.add_schedule(
            ScheduledTournament(
                id="weekly_main",
                name_template="Weekly Tournament - Week {week}",
                description="Main weekly trading competition",
                frequency=ScheduleFrequency.WEEKLY,
                duration_hours=168,  # 1 week
                max_participants=100,
            )
        )

        # Daily blitz tournament
        self.add_schedule(
            ScheduledTournament(
                id="daily_blitz",
                name_template="Daily Blitz - {date}",
                description="Fast-paced daily tournament",
                frequency=ScheduleFrequency.DAILY,
                duration_hours=24,
                max_participants=50,
            )
        )

        # Weekly crypto tournament
        self.add_schedule(
            ScheduledTournament(
                id="weekly_crypto",
                name_template="Crypto Masters - Week {week}",
                description="Cryptocurrency trading tournament",
                frequency=ScheduleFrequency.WEEKLY,
                variant=TournamentVariant.CRYPTO_ONLY,
                duration_hours=168,
                max_participants=75,
            )
        )


# Global scheduler instance
tournament_scheduler = TournamentScheduler()
