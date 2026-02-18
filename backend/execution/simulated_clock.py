import asyncio
from datetime import datetime


class SimulatedClock:
    """
    A simulated clock that allows accelerating time for backtesting.
    """

    def __init__(self, start_time: datetime, speed: float = 1.0):
        self.current_time = start_time
        self.speed = speed
        self._real_start_time = datetime.now()

    async def sleep_until(self, target_time: datetime):
        """
        Sleeps until the target time effectively, scaling by the speed factor.
        """
        if target_time <= self.current_time:
            return

        time_delta = (target_time - self.current_time).total_seconds()

        # In a real backtest, we might not want to actually sleep if speed is infinite (event driven)
        # But for 'replay' mode where we simulate real-time stream at X speed:
        sys_delay = time_delta / self.speed

        if sys_delay > 0:
            await asyncio.sleep(sys_delay)

        self.current_time = target_time

    def now(self) -> datetime:
        return self.current_time
