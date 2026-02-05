"""
Simulated Clock for Backtesting.

Provides time control for historical data replay,
allowing tests to run faster than real-time.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional


class SimulatedClock:
    """
    A controllable clock for backtesting that can run at variable speeds.
    
    Features:
    - Speed multiplier (1x = real-time, 100x = 100x faster)
    - Pause/resume capability
    - Jump to specific timestamps
    """
    
    def __init__(
        self,
        start_time: datetime,
        speed: float = 1.0,
        paused: bool = False
    ):
        """
        Initialize simulated clock.
        
        Args:
            start_time: Starting timestamp for simulation
            speed: Speed multiplier (1.0 = real-time)
            paused: Start in paused state
        """
        self._start_time = start_time
        self._current_time = start_time
        self._speed = speed
        self._paused = paused
        self._real_start = datetime.utcnow()
    
    @property
    def current_time(self) -> datetime:
        """Get current simulated time."""
        return self._current_time
    
    @property
    def speed(self) -> float:
        """Get current speed multiplier."""
        return self._speed
    
    @speed.setter
    def speed(self, value: float) -> None:
        """Set speed multiplier."""
        if value <= 0:
            raise ValueError("Speed must be positive")
        self._speed = value
    
    @property
    def now(self) -> datetime:
        """Alias for current_time."""
        return self._current_time
    
    def advance_by(self, delta: timedelta) -> datetime:
        """
        Advance clock by a time delta.
        
        Args:
            delta: Time to advance
            
        Returns:
            New current time
        """
        self._current_time += delta
        return self._current_time
    
    def advance_to(self, target_time: datetime) -> datetime:
        """
        Advance clock to a specific timestamp.
        
        Args:
            target_time: Target timestamp
            
        Returns:
            New current time
        """
        if target_time < self._current_time:
            raise ValueError("Cannot travel back in time")
        self._current_time = target_time
        return self._current_time
    
    async def sleep(self, seconds: float) -> None:
        """
        Sleep for simulated seconds (adjusted by speed).
        
        Args:
            seconds: Number of simulated seconds to sleep
        """
        if self._paused:
            # Wait for unpause
            while self._paused:
                await asyncio.sleep(0.1)
        
        # Real sleep time is adjusted by speed
        real_seconds = seconds / self._speed
        await asyncio.sleep(real_seconds)
        
        # Advance clock
        self._current_time += timedelta(seconds=seconds)
    
    async def sleep_until(self, target_time: datetime) -> None:
        """
        Sleep until a specific simulated timestamp.
        
        Args:
            target_time: Target timestamp to sleep until
        """
        if target_time <= self._current_time:
            return
        
        delta = (target_time - self._current_time).total_seconds()
        await self.sleep(delta)
    
    def pause(self) -> None:
        """Pause the clock."""
        self._paused = True
    
    def resume(self) -> None:
        """Resume the clock."""
        self._paused = False
    
    def reset(self) -> None:
        """Reset clock to start time."""
        self._current_time = self._start_time
