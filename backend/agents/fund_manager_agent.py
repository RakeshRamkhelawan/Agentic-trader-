"""
FundManagerAgent - Capital Allocation & Position Sizing

Uses Kelly Criterion voor optimal position sizing met safety multipliers.
"""

import logging
from typing import Optional
from datetime import datetime, UTC

from backend.agents.base_agent import BaseAgent
from backend.core.schemas.ooda_types import (
    TradeProposal,
    RiskAssessment,
    PortfolioState,
    CapitalAllocation
)


class FundManagerAgent(BaseAgent):
    """
    Capital allocation agent.
    
    Determines position sizes using Kelly Criterion en portfolio-level
    risk constraints.
    """
    
    def __init__(
        self,
        model_name: str = "gpt-4",
        max_position_pct: float = 0.10,  # 10% max per position
        max_total_exposure: float = 0.90,  # 90% max total exposure
        kelly_multiplier: float = 0.5,  # Half-Kelly safety
        **kwargs
    ):
        """
        Initialize FundManager.
        
        Args:
            model_name: LLM model
            max_position_pct: Max position as % of equity
            max_total_exposure: Max total exposure
            kelly_multiplier: Kelly safety multiplier (0.5 = half-Kelly)
        """
        super().__init__(model_name=model_name, **kwargs)
        self.max_position_pct = max_position_pct
        self.max_total_exposure = max_total_exposure
        self.kelly_multiplier = kelly_multiplier
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def analyze(self, *args, **kwargs):
        """
        BaseAgent abstract method implementation.
        
        FundManager doesn't analyze observations directly,
        but this method is required by BaseAgent interface.
        """
        raise NotImplementedError(
            "FundManager uses allocate_capital() instead of analyze()"
        )
    
    async def allocate_capital(
        self,
        trade_proposal: TradeProposal,
        risk_assessment: RiskAssessment,
        portfolio_state: PortfolioState
    ) -> CapitalAllocation:
        """
        Determine position size voor trade.
        
        Args:
            trade_proposal: Proposed trade
            risk_assessment: Risk assessment
            portfolio_state: Current portfolio state
        
        Returns:
            CapitalAllocation decision
        """
        self.logger.info(
            f"Allocating capital for {trade_proposal.symbol}, "
            f"equity={portfolio_state.total_equity:.2f}"
        )
        
        # Calculate Kelly fraction
        kelly_fraction = self._calculate_kelly(
            win_probability=risk_assessment.win_probability,
            avg_win=self._estimate_avg_win(trade_proposal),
            avg_loss=self._estimate_avg_loss(trade_proposal)
        )
        
        # Apply safety multiplier
        position_fraction = kelly_fraction * self.kelly_multiplier
        
        # Clamp to max position size
        position_fraction = min(position_fraction, self.max_position_pct)
        
        # Check total exposure
        if portfolio_state.total_exposure_pct + position_fraction > self.max_total_exposure:
            # Reduce to fit within exposure limit
            available_exposure = self.max_total_exposure - portfolio_state.total_exposure_pct
            position_fraction = max(0.0, available_exposure)
            
            if position_fraction == 0:
                return CapitalAllocation(
                    position_size_usd=0.0,
                    position_fraction=0.0,
                    kelly_fraction=kelly_fraction,
                    approved=False,
                    reasoning=f"Total exposure limit reached ({portfolio_state.total_exposure_pct:.1%})"
                )
        
        # Calculate position size
        position_size_usd = portfolio_state.total_equity * position_fraction
        
        # Check minimum viable size
        if position_size_usd < 10.0:  # Minimum $10 position
            return CapitalAllocation(
                position_size_usd=0.0,
                position_fraction=0.0,
                kelly_fraction=kelly_fraction,
                approved=False,
                reasoning=f"Position too small: ${position_size_usd:.2f} < $10 minimum"
            )
        
        # Approve allocation
        reasoning = (
            f"Kelly={kelly_fraction:.2%}, "
            f"Applied={position_fraction:.2%} ({self.kelly_multiplier}x Kelly), "
            f"Size=${position_size_usd:.2f}"
        )
        
        self.logger.info(f"Allocation approved: {reasoning}")
        
        return CapitalAllocation(
            position_size_usd=position_size_usd,
            position_fraction=position_fraction,
            kelly_fraction=kelly_fraction,
            approved=True,
            reasoning=reasoning
        )
    
    def _calculate_kelly(
        self,
        win_probability: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Calculate Kelly Criterion optimal fraction.
        
        Formula: f* = (p*W - (1-p)*L) / W
        
        Where:
        - p = win probability
        - W = average win (% gain)
        - L = average loss (% loss, positive number)
        
        Args:
            win_probability: Probability of winning
            avg_win: Average win percentage
            avg_loss: Average loss percentage
        
        Returns:
            Kelly fraction (0-1)
        """
        if avg_win <= 0:
            return 0.0
        
        if avg_loss < 0:
            avg_loss = abs(avg_loss)
        
        # Kelly formula
        numerator = (win_probability * avg_win) - ((1 - win_probability) * avg_loss)
        kelly = numerator / avg_win
        
        # Clamp to [0, 1]
        kelly = max(0.0, min(kelly, 1.0))
        
        return kelly
    
    def _estimate_avg_win(self, proposal: TradeProposal) -> float:
        """
        Estimate average win percentage from proposal.
        
        Args:
            proposal: Trade proposal
        
        Returns:
            Estimated avg win %
        """
        if proposal.entry_price is None or proposal.entry_price == 0:
            # Use current price as proxy
            entry = proposal.stop_loss * 1.01  # Assume slightly above stop
        else:
            entry = proposal.entry_price
        
        # Calculate potential gain to take profit
        if proposal.side == "buy":
            potential_gain = (proposal.take_profit - entry) / entry
        else:  # sell
            potential_gain = (entry - proposal.take_profit) / entry
        
        return max(0.0, potential_gain)
    
    def _estimate_avg_loss(self, proposal: TradeProposal) -> float:
        """
        Estimate average loss percentage from proposal.
        
        Args:
            proposal: Trade proposal
        
        Returns:
            Estimated avg loss % (positive number)
        """
        if proposal.entry_price is None or proposal.entry_price == 0:
            entry = proposal.stop_loss * 1.01
        else:
            entry = proposal.entry_price
        
        # Calculate potential loss to stop loss
        if proposal.side == "buy":
            potential_loss = (entry - proposal.stop_loss) / entry
        else:  # sell
            potential_loss = (proposal.stop_loss - entry) / entry
        
        return abs(potential_loss)
