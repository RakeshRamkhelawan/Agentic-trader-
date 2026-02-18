"""
Analysis Service
Orchestrates analysis engines and data persistence.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from src.analysis import MakerTakerAnalyzer, StatisticalTestsFramework, VolumeTrendsAnalyzer
from src.db.duckdb_manager import DuckDBManager
from src.signals import SignalGenerator

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Orchestrates market analysis pipeline.

    Coordinates:
    - Data ingestion
    - Analysis execution
    - Signal generation
    - Result persistence

    Usage:
        service = AnalysisService(db_manager=manager)
        result = await service.analyze_market(
            ticker="TRUMP25",
            trades_df=df
        )
    """

    def __init__(self, db_manager: Optional[DuckDBManager] = None):
        """
        Initialize analysis service.

        Args:
            db_manager: DuckDB manager for result persistence
        """
        self.db_manager = db_manager
        self.mt_analyzer = MakerTakerAnalyzer()
        self.vol_analyzer = VolumeTrendsAnalyzer()
        self.stat_framework = StatisticalTestsFramework()
        self.signal_generator = SignalGenerator()

    def analyze_market(
        self,
        market: str,
        symbol: str,
        trades_df: pd.DataFrame,
        category: str = "politics",
    ) -> dict:
        """
        Perform comprehensive market analysis.

        Args:
            market: Market name
            symbol: Trading symbol
            trades_df: DataFrame with trade data
            category: Market category

        Returns:
            Dict with analysis results
        """
        logger.info(f"Starting analysis for {market} ({symbol})")

        # Check minimum data
        if len(trades_df) < 10:
            logger.warning(f"Insufficient trades for {market}: {len(trades_df)}")
            return {
                "market": market,
                "symbol": symbol,
                "status": "insufficient_data",
                "message": f"Only {len(trades_df)} trades (need 10+)",
            }

        results = {
            "market": market,
            "symbol": symbol,
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Run spread analysis
        try:
            spread_metrics = self.mt_analyzer.analyze_market(trades_df)
            if spread_metrics:
                results["spread_metrics"] = spread_metrics.to_dict()
                logger.info(
                    f"Spread analysis complete: {spread_metrics.liquidity_score:.1f}/100 liquidity"
                )
            else:
                results["spread_metrics"] = None
        except Exception as e:
            logger.error(f"Spread analysis failed: {e}")
            results["spread_metrics"] = None

        # Run volume analysis
        try:
            volume_metrics = self.vol_analyzer.analyze_market(
                trades_df,
                volume_col="volume" if "volume" in trades_df.columns else "amount",
            )
            if volume_metrics:
                results["volume_metrics"] = volume_metrics.to_dict()
                logger.info(
                    f"Volume analysis complete: {volume_metrics.volume_trend} trend"
                )
            else:
                results["volume_metrics"] = None
        except Exception as e:
            logger.error(f"Volume analysis failed: {e}")
            results["volume_metrics"] = None

        # Run statistical tests
        try:
            if "yes_price" in trades_df.columns:
                price_series = trades_df["yes_price"]
            elif "price" in trades_df.columns:
                price_series = trades_df["price"]
            else:
                price_series = None

            if price_series is not None:
                price_tests = {
                    "normality_test": self.stat_framework.test_normality(
                        price_series
                    ).to_dict(),
                    "stationarity_test": self.stat_framework.test_stationarity(
                        price_series
                    ).to_dict(),
                }
                results["statistical_tests"] = price_tests
                logger.info("Statistical tests complete")
            else:
                results["statistical_tests"] = None
        except Exception as e:
            logger.error(f"Statistical analysis failed: {e}")
            results["statistical_tests"] = None

        # Generate signals
        try:
            signals = self.signal_generator.generate_signals(
                market=market,
                symbol=symbol,
                analysis_results={
                    "spread_metrics": results.get("spread_metrics"),
                    "volume_metrics": results.get("volume_metrics"),
                    "test_results": results.get("statistical_tests", {}),
                },
            )

            # Rank and serialize signals
            ranked_signals = self.signal_generator.rank_signals(signals)
            results["signals"] = [s.to_dict() for s in ranked_signals]
            logger.info(f"Generated {len(ranked_signals)} signals")
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            results["signals"] = []

        # Store in database if available
        if self.db_manager and self.db_manager.is_initialized:
            self._persist_results(results)

        return results

    def _persist_results(self, results: dict) -> None:
        """
        Persist analysis results to database.

        Args:
            results: Analysis results dictionary
        """
        try:
            # Store signals in database
            signals = results.get("signals", [])
            if signals:
                signals_data = []
                for signal in signals:
                    signals_data.append(
                        {
                            "signal_id": signal["signal_id"],
                            "market": signal["market"],
                            "category": signal["category"],
                            "signal_type": signal["signal_type"],
                            "confidence": signal["confidence"],
                            "symbol": signal["symbol"],
                            "indicators": json.dumps(signal["indicators"]),
                        }
                    )

                signals_df = pd.DataFrame(signals_data)
                self.db_manager.insert_dataframe("generated_signals", signals_df)
                logger.info(f"Persisted {len(signals)} signals to database")

            # Store analysis results
            analysis_data = {
                "analysis_id": f"analysis_{results['market'].replace(' ', '_')}_{datetime.now().timestamp()}",
                "analysis_type": "comprehensive",
                "market": results["market"],
                "status": "completed",
                "result": json.dumps(
                    {
                        "spread_metrics": results.get("spread_metrics"),
                        "volume_metrics": results.get("volume_metrics"),
                        "statistical_tests": results.get("statistical_tests"),
                    }
                ),
                "completed_at": datetime.now(timezone.utc),
            }

            analysis_df = pd.DataFrame([analysis_data])
            self.db_manager.insert_dataframe("analysis_results", analysis_df)
            logger.info("persisted analysis results to database")

        except Exception as e:
            logger.error(f"Failed to persist results: {e}")

    def get_market_efficiency_score(self, trades_df: pd.DataFrame) -> float:
        """
        Calculate overall market efficiency score.

        Args:
            trades_df: Market trade data

        Returns:
            Efficiency score (0-100)
        """
        efficiency = self.mt_analyzer.calculate_market_efficiency(trades_df)
        activity = self.vol_analyzer.calculate_market_activity(trades_df)

        # Combined score (60% efficiency, 40% activity)
        return efficiency * 0.6 + activity * 0.4

    def compare_markets(self, markets_data: dict[str, pd.DataFrame]) -> dict[str, dict]:
        """
        Compare metrics across multiple markets.

        Args:
            markets_data: Dict of market_name -> DataFrame

        Returns:
            Dict with comparative metrics
        """
        results = {}

        for market_name, df in markets_data.items():
            if len(df) < 10:
                continue

            spread_metrics = self.mt_analyzer.analyze_market(df)
            volume_metrics = self.vol_analyzer.analyze_market(df)
            efficiency = self.get_market_efficiency_score(df)

            results[market_name] = {
                "trades_count": len(df),
                "liquidity_score": (
                    spread_metrics.liquidity_score if spread_metrics else 0
                ),
                "volume_trend": (
                    volume_metrics.volume_trend if volume_metrics else "unknown"
                ),
                "efficiency_score": efficiency,
            }

        return results
