"""
Tests for KellyPositionSizer.
"""

import pytest
from backend.core.risk.kelly import KellyPositionSizer

class TestKellyPositionSizer:

    def setup_method(self):
        # Default parameters: 25% Kelly (quarter-Kelly), max 10% position cap
        self.sizer = KellyPositionSizer(default_kelly_fraction=0.25, max_position=0.1)
        
    def test_ideal_kelly_calculation(self):
        """
        Test a standard winning scenario:
        - Win rate: 60%
        - Avg win: 10%
        - Avg loss: 5%
        => b (reward/risk) = 2.0
        => Full Kelly = (0.6 * 2.0 - 0.4) / 2.0 = 0.8 / 2.0 = 0.4
        => Quarter Kelly (25%) = 0.4 * 0.25 = 0.1
        Max Cap is 10%, so it should return exactly 0.1
        """
        size = self.sizer.calculate_size(
            win_rate=0.6,
            avg_win=0.10,
            avg_loss=0.05
        )
        assert abs(size - 0.10) < 0.0001
        
    def test_capped_position(self):
        """
        Test that a very high Kelly allocation is still capped by max_position.
        Win rate: 90%
        Avg win: 20%
        Avg loss: 5% (b = 4.0)
        Full Kelly = (0.9 * 4 - 0.1) / 4 = 3.5 / 4 = 0.875
        Quarter Kelly = 0.21875
        Since max cap = 0.1, it should clamp to 0.1
        """
        size = self.sizer.calculate_size(
            win_rate=0.9,
            avg_win=0.20,
            avg_loss=0.05
        )
        assert size == 0.10
        
    def test_negative_edge(self):
        """
        Test a losing strategy where Kelly should return 0.0.
        Win rate: 40%
        Avg win: 5%
        Avg loss: 10% (b = 0.5)
        Kelly = (0.4 * 0.5 - 0.6) / 0.5 = (0.2 - 0.6) / 0.5 = -0.8
        Should return 0.0
        """
        size = self.sizer.calculate_size(
            win_rate=0.4,
            avg_win=0.05,
            avg_loss=0.10
        )
        assert size == 0.0
        
    def test_zero_loss(self):
        """If average loss is zero, we cannot compute b, return 0.0."""
        size = self.sizer.calculate_size(
            win_rate=1.0,
            avg_win=0.10,
            avg_loss=0.0
        )
        assert size == 0.0
        
    def test_custom_fraction_override(self):
        """Test passing a custom kelly fraction during the call."""
        # Using the ideal ratio scenario (Full Kelly = 0.4)
        # Using Half Kelly (0.5), we expect 0.2, but the default max cap is 0.1.
        # So we also override max cap.
        size = self.sizer.calculate_size(
            win_rate=0.6,
            avg_win=0.10,
            avg_loss=0.05,
            kelly_fraction=0.5,
            max_position=0.5  # Allow up to 50%
        )
        assert abs(size - 0.20) < 0.0001
