"""
Sentiment Scorer for Consensus Engine integration.

Produces a normalized score (-1.0 to 1.0) that indicates how well
market sentiment aligns with a proposed trade direction.
"""


class SentimentScorer:
    """
    Computes a sentiment-based support score for a trade proposal.

    Takes raw sentiment data (score, news_impact) and the proposed
    trade direction, then returns an alignment-adjusted score suitable
    for use as a Vote in the TradingConsensusEngine.
    """

    def score(
        self,
        sentiment_value: float,
        news_impact: float,
        proposed_side: str,
    ) -> float:
        """
        Calculate the sentiment support score for a proposed trade.

        Args:
            sentiment_value: Raw sentiment score from -1.0 (very bearish)
                             to 1.0 (very bullish).
            news_impact: News impact score from -1.0 (very negative news)
                         to 1.0 (very positive news).
            proposed_side: "buy" or "sell".

        Returns:
            Support score from -1.0 (strongly against proposal) to
            1.0 (strongly supports proposal).
        """
        # Combine sentiment and news (70/30 weighting)
        raw_score = sentiment_value * 0.7 + news_impact * 0.3

        # Align with proposed direction:
        # For a BUY proposal, positive sentiment supports it.
        # For a SELL proposal, negative sentiment supports it.
        if proposed_side == "sell":
            aligned_score = -raw_score
        else:
            aligned_score = raw_score

        # Clamp to [-1.0, 1.0]
        return max(-1.0, min(1.0, aligned_score))
