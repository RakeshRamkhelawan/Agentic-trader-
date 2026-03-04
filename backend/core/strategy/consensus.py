"""
Trading Consensus Engine.

Aggregates votes from various signal providers (Technical, MTF, Risk, Sentiment)
to formulate a final decision on trading proposals. This moves the system from
a single-indicator decision model to an ensemble voting model.
"""

import logging
from typing import TypedDict

logger = logging.getLogger(__name__)


class Vote(TypedDict):
    """Represents a vote from a signal provider."""
    provider: str
    score: float       # -1.0 (Strong Reject) to 1.0 (Strong Approve)
    reasoning: str


class ConsensusResult(TypedDict):
    """The result of the consensus evaluation."""
    approved: bool
    score: float       # -1.0 to 1.0
    threshold: float
    votes: list[Vote]
    reasoning: str


class TradingConsensusEngine:
    """
    Evaluates trade proposals using an ensemble of weighted votes.
    """

    # Static weight configuration for signal providers. Sum should ideally be 1.0
    PROVIDER_WEIGHTS = {
        "technical_strategy": 0.40,  # The primary strategy (e.g. EnhancedMomentum)
        "mtf_analyzer": 0.30,        # Multi-timeframe trend alignment
        "risk_manager": 0.30,        # Risk & Portfolio context
    }

    # If the score drops below this, it's a VETO (regardless of positive weight sum)
    VETO_THRESHOLD = -0.8

    def __init__(self, approval_threshold: float = 0.20):
        """
        Args:
            approval_threshold: The minimum composite score required to approve a trade.
        """
        self.approval_threshold = approval_threshold

    def evaluate_proposal(self, votes: list[Vote]) -> ConsensusResult:
        """
        Evaluate a list of votes and return a consensus decision.

        Args:
            votes: List of Vote dictionaries.

        Returns:
            ConsensusResult dict containing the decision and aggregated scores.
        """
        if not votes:
             return {
                 "approved": False,
                 "score": 0.0,
                 "threshold": self.approval_threshold,
                 "votes": [],
                 "reasoning": "No votes provided."
             }

        total_score = 0.0
        applied_weight = 0.0
        reasoning_parts = []
        is_vetoed = False
        veto_reason = ""

        # Normalize provider names to config keys for matching
        # Assuming provider names match the keys exactly for this simple config
        for vote in votes:
            provider = vote["provider"]
            score = vote["score"]
            
            # Check for absolute veto from any provider
            if score <= self.VETO_THRESHOLD:
                is_vetoed = True
                veto_reason = f"VETO by {provider}: {vote.get('reasoning', '')}"
                logger.warning(veto_reason)
                # We continue to calculate the final mathematical score for logging,
                # but the approval will ultimately be False.

            weight = self.PROVIDER_WEIGHTS.get(provider, 0.0)
            if weight == 0.0:
                logger.warning("Unrecognized vote provider: %s, weight 0.0 applied.", provider)

            total_score += score * weight
            applied_weight += weight
            reasoning_parts.append(f"{provider}({score:.2f})")

        # Normalize score to -1.0 to 1.0 range based on applied weights
        # This handles cases where some providers didn't vote
        if applied_weight > 0.0:
            final_score = total_score / applied_weight
        else:
            final_score = 0.0

        approved = False
        if is_vetoed:
            reasoning = veto_reason
        elif final_score >= self.approval_threshold:
            approved = True
            reasoning = f"APPROVED. Composite score {final_score:.2f} >= threshold {self.approval_threshold:.2f}. Breakdown: " + ", ".join(reasoning_parts)
        else:
            reasoning = f"REJECTED. Composite score {final_score:.2f} < threshold {self.approval_threshold:.2f}. Breakdown: " + ", ".join(reasoning_parts)

        return {
            "approved": approved,
            "score": round(final_score, 4),
            "threshold": self.approval_threshold,
            "votes": votes,
            "reasoning": reasoning
        }
