from datetime import datetime, time
from typing import Optional

class RahuKalaGate:
    """
    Enforces 'Rahu Kala' (Poison Time) restrictions.
    In Vedic astrology, this is a daily period of approx 1.5 hours 
    considered inauspicious for starting new ventures (trade entry).
    """

    # Standard Rahu Kala Times (approximate, assuming 6:00 AM Sunrise)
    # Day: (Start Hour, Start Minute, End Hour, End Minute)
    # Mon:  7:30 -  9:00
    # Tue: 15:00 - 16:30
    # Wed: 12:00 - 13:30
    # Thu: 13:30 - 15:00
    # Fri: 10:30 - 12:00
    # Sat:  9:00 - 10:30
    # Sun: 16:30 - 18:00
    
    RAHU_KALA_SCHEDULE = {
        0: (7, 30, 9, 0),    # Monday
        1: (15, 0, 16, 30),  # Tuesday
        2: (12, 0, 13, 30),  # Wednesday
        3: (13, 30, 15, 0),  # Thursday
        4: (10, 30, 12, 0),  # Friday
        5: (9, 0, 10, 30),   # Saturday
        6: (16, 30, 18, 0),  # Sunday
    }

    def is_in_rahu_kala(self, dt: datetime) -> bool:
        """
        Check if the given datetime falls within Rahu Kala.
        """
        day_of_week = dt.weekday()
        current_time = dt.time()
        
        schedule = self.RAHU_KALA_SCHEDULE.get(day_of_week)
        if not schedule:
            return False
            
        start_h, start_m, end_h, end_m = schedule
        
        start_time = time(start_h, start_m)
        end_time = time(end_h, end_m)
        
        return start_time <= current_time < end_time

    def can_enter_trade(self, dt: datetime, emergency_override: bool = False) -> bool:
        """
        Determines if a trade can be entered.
        Blocks entry during Rahu Kala unless emergency override is True.
        """
        if emergency_override:
            return True
            
        if self.is_in_rahu_kala(dt):
            return False
            
        return True
