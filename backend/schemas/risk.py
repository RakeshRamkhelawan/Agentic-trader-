from enum import Enum

from pydantic import BaseModel, Field


class AutonomyStatus(str, Enum):
    """
    Level of agent autonomy.
    """

    MANUAL = "MANUAL"  # Agent advises, Human clicks approve
    SEMI_AUTO = "SEMI_AUTO"  # Agent acts within small limits, asks for big ones
    FULL_AUTO = "FULL_AUTO"  # Agent acts fully, blocked only by Hard Risk Limits


class RiskProfile(BaseModel):
    """
    User-configurable risk limits.
    """

    max_daily_loss: float = Field(..., gt=0, description="Max allowed loss per day in EUR")
    max_order_size: float = Field(..., gt=0, description="Max value of a single order in EUR")
    max_open_positions: int = Field(5, ge=1, le=20, description="Max concurrent open trades")

    # Asset Controls
    allowed_assets: list[str] = Field(
        default_factory=list,
        description="Whitelist of symbols (e.g. ['BTC-EUR', 'ETH-EUR'])",
    )
    blacklisted_assets: list[str] = Field(default_factory=list, description="Blacklist of symbols")

    # Safety
    kill_switch_enabled: bool = Field(False, description="If True, NO new orders are allowed")

    # Advanced
    max_drawdown_pct: float = Field(
        5.0, description="Max portfolio drawdown percentage before stopping"
    )
