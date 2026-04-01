"""
Tests voor MultiTimeframeAnalyzer.
"""

from backend.core.indicators.mtf import MultiTimeframeAnalyzer


class TestMultiTimeframeAnalyzer:

    def test_empty_data_returns_zero(self):
        """Met geen data moet de score 0.0 zijn."""
        score = MultiTimeframeAnalyzer.analyze_macro_trend({})
        assert score == 0.0

    def test_missing_timeframes_normalizes_correctly(self):
        """Ontbrekende timeframes worden correct genormaliseerd o.b.v. toegepaste gewichten."""
        # Alleen 1d data (weight 0.35).
        # Prijs gaat hard omhoog -> strong uptrend -> 1.0 direction.
        # Score moet 1.0 zijn (genormaliseerd (1.0 * 0.35) / 0.35 = 1.0).
        uptrend = [100.0 + i for i in range(100)]
        data = {"1d": uptrend}

        score = MultiTimeframeAnalyzer.analyze_macro_trend(data)
        assert score == 1.0

    def test_mixed_trends(self):
        """Mixed trends geven een tussentijdse score."""
        uptrend = [100.0 + i for i in range(100)]
        downtrend = [100.0 - i for i in range(100)]

        # 1d is uptrend (+1.0 * 0.35)
        # 4h is uptrend (+1.0 * 0.30)
        # 1h is uptrend (+1.0 * 0.20)
        # 15m is downtrend (-1.0 * 0.10)
        # 5m is downtrend (-1.0 * 0.05)
        # Total applied weight = 1.0
        # Expected score: 0.35 + 0.30 + 0.20 - 0.10 - 0.05 = 0.70
        data = {
            "1d": uptrend,
            "4h": uptrend,
            "1h": uptrend,
            "15m": downtrend,
            "5m": downtrend,
        }

        score = MultiTimeframeAnalyzer.analyze_macro_trend(data)
        assert score == 0.70

    def test_rsi_lag_gives_partial_score(self):
        """Als EMAs aligned zijn maar RSI nog achterblijft, wordt er een gedeeltelijke score van 0.5 (of -0.5) gegeven."""
        # Creëer situatie waar EMA bearish aligned is, maar RSI net boven 50
        # Dit doen we door een downtrend te simuleren gevolgd door een sterke recente bump omhoog
        # De EMAs zijn traag (55 period) en reageren nog op de downtrend
        # De RSI (14 period) reageert sneller op de recente spike

        downtrend = [200.0 - i for i in range(60)]  # EMA 8, 21, 55 reageren
        recent_spike = [
            142.0 + i for i in range(10)
        ]  # Korte krachtige stijging, trekt RSI naar boven
        prices = downtrend + recent_spike

        data = {"1h": prices}
        score = MultiTimeframeAnalyzer.analyze_macro_trend(data)

        # Verwachten gedeeltelijke score negatief wegens EMA bearish maar RSI >= 50
        assert score == -0.5

    def test_too_little_data_returns_zero(self):
        """Als een timeframe < 55 data points heeft (te weinig voor EMA 55), wordt deze genegeerd."""
        prices_short = [100.0] * 50  # length 50
        data = {"1d": prices_short}

        score = MultiTimeframeAnalyzer.analyze_macro_trend(data)
        assert score == 0.0

    def test_strong_downtrend_all_timeframes(self):
        """Alle timeframes in sterke downtrend = -1.0."""
        downtrend = [200.0 - i for i in range(100)]
        data = {tf: downtrend for tf in MultiTimeframeAnalyzer.TIMEFRAME_WEIGHTS}

        score = MultiTimeframeAnalyzer.analyze_macro_trend(data)
        assert score == -1.0
