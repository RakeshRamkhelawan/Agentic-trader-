"""
Tests for SentimentScorer.
"""

from backend.core.strategy.sentiment_scorer import SentimentScorer


class TestSentimentScorer:

    def setup_method(self):
        self.scorer = SentimentScorer()

    def test_bullish_sentiment_supports_buy(self):
        """Positive sentiment should support a buy proposal."""
        score = self.scorer.score(
            sentiment_value=0.8, news_impact=0.5, proposed_side="buy"
        )
        assert score > 0.5

    def test_bearish_sentiment_supports_sell(self):
        """Negative sentiment should support a sell proposal (flipped)."""
        score = self.scorer.score(
            sentiment_value=-0.8, news_impact=-0.5, proposed_side="sell"
        )
        # Negative sentiment + sell => aligned => positive score
        assert score > 0.5

    def test_sentiment_contradicts_buy(self):
        """Strongly bearish sentiment should contradict a buy proposal."""
        score = self.scorer.score(
            sentiment_value=-0.9, news_impact=-0.7, proposed_side="buy"
        )
        assert score < -0.5

    def test_neutral_sentiment(self):
        """Neutral sentiment should produce a near-zero score."""
        score = self.scorer.score(
            sentiment_value=0.0, news_impact=0.0, proposed_side="buy"
        )
        assert abs(score) < 0.01

    def test_news_impact_weight(self):
        """News impact should contribute 30% to the final score."""
        # Pure news impact, no sentiment
        score = self.scorer.score(
            sentiment_value=0.0, news_impact=1.0, proposed_side="buy"
        )
        assert abs(score - 0.3) < 0.01

    def test_clamping(self):
        """Score should be clamped to [-1.0, 1.0]."""
        score = self.scorer.score(
            sentiment_value=1.0, news_impact=1.0, proposed_side="buy"
        )
        assert score == 1.0

        score_neg = self.scorer.score(
            sentiment_value=1.0, news_impact=1.0, proposed_side="sell"
        )
        assert score_neg == -1.0
