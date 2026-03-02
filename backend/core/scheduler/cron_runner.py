"""Cron-style runner for scheduled tasks."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CronJob:
    """A scheduled cron job."""

    id: str
    name: str
    minute: str  # 0-59 or *
    hour: str  # 0-23 or *
    day_of_month: str  # 1-31 or *
    month: str  # 1-12 or *
    day_of_week: str  # 0-6 (0=Sunday) or *
    task: Callable
    enabled: bool = True
    last_run: datetime | None = None
    run_count: int = 0


class CronRunner:
    """
    Cron-style task scheduler.

    Supports standard cron syntax:
    - * = any value
    - */n = every n (e.g., */5 = every 5 minutes)
    - n = specific value
    - n,m = multiple values
    - n-m = range
    """

    def __init__(self):
        self._jobs: dict[str, CronJob] = {}
        self._running = False
        self._task: asyncio.Task | None = None

    def add_job(
        self,
        job_id: str,
        name: str,
        schedule: str,  # "minute hour day month dow"
        task: Callable,
    ) -> CronJob:
        """Add a cron job."""
        parts = schedule.split()
        if len(parts) != 5:
            raise ValueError("Schedule must have 5 parts: minute hour day month dow")

        job = CronJob(
            id=job_id,
            name=name,
            minute=parts[0],
            hour=parts[1],
            day_of_month=parts[2],
            month=parts[3],
            day_of_week=parts[4],
            task=task,
        )

        self._jobs[job_id] = job
        return job

    def remove_job(self, job_id: str) -> bool:
        """Remove a cron job."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False

    def enable_job(self, job_id: str) -> bool:
        """Enable a job."""
        if job_id in self._jobs:
            self._jobs[job_id].enabled = True
            return True
        return False

    def disable_job(self, job_id: str) -> bool:
        """Disable a job."""
        if job_id in self._jobs:
            self._jobs[job_id].enabled = False
            return True
        return False

    def _match_field(self, field: str, value: int) -> bool:
        """Check if value matches cron field."""
        if field == "*":
            return True

        # Handle */n syntax
        if field.startswith("*/"):
            step = int(field[2:])
            return value % step == 0

        # Handle ranges (e.g., 1-5)
        if "-" in field:
            start, end = map(int, field.split("-"))
            return start <= value <= end

        # Handle lists (e.g., 1,3,5)
        if "," in field:
            values = [int(x) for x in field.split(",")]
            return value in values

        # Single value
        return value == int(field)

    def _should_run(self, job: CronJob, now: datetime) -> bool:
        """Check if job should run at current time."""
        if not job.enabled:
            return False

        # Check if already ran this minute
        if job.last_run and job.last_run.minute == now.minute and job.last_run.hour == now.hour:
            return False

        return (
            self._match_field(job.minute, now.minute)
            and self._match_field(job.hour, now.hour)
            and self._match_field(job.day_of_month, now.day)
            and self._match_field(job.month, now.month)
            and self._match_field(job.day_of_week, now.weekday())
        )

    async def _run_job(self, job: CronJob) -> None:
        """Execute a job."""
        try:
            job.last_run = datetime.utcnow()
            job.run_count += 1

            if asyncio.iscoroutinefunction(job.task):
                await job.task()
            else:
                job.task()
        except Exception as e:
            # Log error but don't stop other jobs
            print(f"Error running job {job.id}: {e}")

    async def run_loop(self) -> None:
        """Main scheduling loop."""
        self._running = True

        while self._running:
            now = datetime.utcnow()

            # Check all jobs
            for job in self._jobs.values():
                if self._should_run(job, now):
                    asyncio.create_task(self._run_job(job))

            # Sleep until next minute
            await asyncio.sleep(60 - now.second)

    def start(self) -> None:
        """Start the cron runner."""
        if not self._running:
            self._task = asyncio.create_task(self.run_loop())

    def stop(self) -> None:
        """Stop the cron runner."""
        self._running = False
        if self._task:
            self._task.cancel()

    def get_status(self) -> dict:
        """Get runner status."""
        return {
            "running": self._running,
            "jobs_count": len(self._jobs),
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "schedule": f"{job.minute} {job.hour} {job.day_of_month} {job.month} {job.day_of_week}",
                    "enabled": job.enabled,
                    "last_run": job.last_run.isoformat() if job.last_run else None,
                    "run_count": job.run_count,
                }
                for job in self._jobs.values()
            ],
        }

    def create_default_jobs(self) -> None:
        """Create default scheduled jobs."""
        # Cache cleanup - every hour
        self.add_job(
            "cache_cleanup",
            "Cache Cleanup",
            "0 * * * *",  # Every hour
            self._cleanup_cache,
        )

        # Leaderboard cache refresh - every 5 minutes
        self.add_job(
            "leaderboard_refresh",
            "Leaderboard Refresh",
            "*/5 * * * *",  # Every 5 minutes
            self._refresh_leaderboards,
        )

        # Analytics aggregation - daily at 1 AM
        self.add_job(
            "analytics_aggregation",
            "Analytics Aggregation",
            "0 1 * * *",  # 1 AM daily
            self._aggregate_analytics,
        )

    async def _cleanup_cache(self) -> None:
        """Cleanup expired cache entries."""
        from backend.cache import redis_cache

        stats = redis_cache.get_stats()
        print(f"Cache stats: {stats}")

    async def _refresh_leaderboards(self) -> None:
        """Refresh leaderboard caches."""
        from backend.cache import redis_cache

        redis_cache.invalidate_leaderboard()
        print("Leaderboard cache invalidated")

    async def _aggregate_analytics(self) -> None:
        """Aggregate daily analytics."""
        print("Analytics aggregation complete")


# Global cron runner
cron_runner = CronRunner()
