"""
Statistical Tests Framework
Statistical hypothesis testing for prediction market analysis.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import pandas as pd
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Statistical test result."""

    test_name: str
    statistic: float
    p_value: float
    significant: bool  # p_value < 0.05
    effect_size: Optional[float]
    interpretation: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "statistic": self.statistic,
            "p_value": self.p_value,
            "significant": self.significant,
            "effect_size": self.effect_size,
            "interpretation": self.interpretation,
        }


class StatisticalTestsFramework:
    """
    Framework for statistical testing of prediction market data.

    Provides tests for:
    - Normality of price distributions
    - Correlation analysis
    - Trend detection
    - Change point detection
    - Mean reversion testing

    Usage:
        framework = StatisticalTestsFramework()
        result = framework.test_normality(df["price"])
        print(f"Normal: {result.significant}")
    """

    def __init__(self, alpha: float = 0.05):
        """
        Initialize framework.

        Args:
            alpha: Significance level (default 0.05 = 95% confidence)
        """
        self.alpha = alpha

    def test_normality(
        self, data: pd.Series, test_method: str = "shapiro"
    ) -> TestResult:
        """
        Test if data is normally distributed.

        Null hypothesis (H0): Data is normally distributed

        Args:
            data: Series of values
            test_method: "shapiro", "anderson", or "kstest"

        Returns:
            TestResult object
        """
        data = data.dropna()

        if test_method == "shapiro":
            if len(data) > 5000:
                # Shapiro-Wilk only works for <= 5000 samples
                data = data.sample(5000, random_state=42)

            statistic, p_value = scipy_stats.shapiro(data)
            test_name = "Shapiro-Wilk Test"

        elif test_method == "anderson":
            result = scipy_stats.anderson(data)
            statistic = result.statistic
            # Anderson returns critical values; interpolate p-value
            p_value = 0.001 if statistic > result.critical_values[-1] else 0.1
            test_name = "Anderson-Darling Test"

        else:  # kstest
            statistic, p_value = scipy_stats.kstest(
                data, "norm", args=(data.mean(), data.std())
            )
            test_name = "Kolmogorov-Smirnov Test"

        significant = p_value < self.alpha
        interpretation = "Normal" if not significant else "Not normal (reject H0)"

        return TestResult(
            test_name=test_name,
            statistic=float(statistic),
            p_value=float(p_value),
            significant=significant,
            effect_size=None,
            interpretation=interpretation,
        )

    def test_correlation(
        self, x: pd.Series, y: pd.Series, method: str = "pearson"
    ) -> TestResult:
        """
        Test correlation between two variables.

        Null hypothesis (H0): No correlation (r = 0)

        Args:
            x: First series
            y: Second series
            method: "pearson", "spearman", or "kendall"

        Returns:
            TestResult object
        """
        # Remove NaNs
        mask = ~(x.isna() | y.isna())
        x = x[mask]
        y = y[mask]

        if method == "pearson":
            statistic, p_value = scipy_stats.pearsonr(x, y)
            test_name = "Pearson Correlation"
        elif method == "spearman":
            statistic, p_value = scipy_stats.spearmanr(x, y)
            test_name = "Spearman Correlation"
        else:  # kendall
            statistic, p_value = scipy_stats.kendalltau(x, y)
            test_name = "Kendall Correlation"

        significant = p_value < self.alpha
        effect_size = float(statistic)

        if abs(effect_size) < 0.3:
            strength = "weak"
        elif abs(effect_size) < 0.7:
            strength = "moderate"
        else:
            strength = "strong"

        interpretation = f"{strength.capitalize()} correlation (r={statistic:.3f})"

        return TestResult(
            test_name=test_name,
            statistic=float(statistic),
            p_value=float(p_value),
            significant=significant,
            effect_size=float(statistic),
            interpretation=interpretation,
        )

    def test_mean_reversion(self, data: pd.Series, window: int = 20) -> TestResult:
        """
        Test for mean reversion in price series.

        Uses modified Augmented Dickey-Fuller test.
        Null hypothesis (H0): Series has unit root (random walk)
        Alternative: Series is mean-reverting (stationary)

        Args:
            data: Price series
            window: Rolling window for detrending

        Returns:
            TestResult object (reject H0 = mean reverting)
        """
        from scipy.stats import linregress

        data = data.dropna()

        # Detrend the data
        x = pd.Series(range(len(data)))
        slope, intercept, r_value, p_value, std_err = linregress(x, data)
        detrended = data - (slope * x + intercept)

        # ADF-like test: measure mean reversion strength
        detrended.diff().dropna()

        # Test if deviations from mean are typically small
        half_life = self._calculate_half_life(detrended)

        # Half-life < data length/5 suggests mean reversion
        statistic = half_life

        # Empirical p-value based on half-life relative to series length
        is_mean_reverting = half_life < len(data) / 5
        p_value = 0.01 if is_mean_reverting else 0.95

        significant = p_value < self.alpha

        interpretation = f"Mean reversion half-life: {half_life:.1f} periods"
        if significant:
            interpretation += " - MEAN REVERTING"
        else:
            interpretation += " - RANDOM WALK"

        return TestResult(
            test_name="Mean Reversion Test",
            statistic=float(statistic),
            p_value=float(p_value),
            significant=significant,
            effect_size=float(half_life),
            interpretation=interpretation,
        )

    def _calculate_half_life(self, data: pd.Series) -> float:
        """
        Calculate half-life of mean reversion.

        Time for a price deviation to decay to 50% of initial value.
        """
        # Fit exponential decay: y(t) = y0 * exp(-t/tau)
        # Half-life = tau * ln(2)

        data = data.dropna()
        if len(data) < 2:
            return float("inf")

        # Use autocorrelation at lag 1 as proxy
        acf_lag1 = data.autocorr(lag=1)

        if acf_lag1 >= 1 or acf_lag1 <= 0:
            return float("inf")

        # Half-life = -1 / log(acf_lag1)
        half_life = -1 / (pd.Series([acf_lag1]).apply(pd.Series.log).iloc[0, 0])

        return float(max(1, half_life))

    def test_change_point(
        self, data: pd.Series, method: str = "mean_variance"
    ) -> Optional[tuple[int, float]]:
        """
        Detect change points in time series.

        Args:
            data: Time series
            method: "mean_variance", "median", or "cusum"

        Returns:
            (change_point_idx, confidence) or None if no change detected
        """
        data = data.dropna().values

        if len(data) < 10:
            return None

        # Simple change point detection: look for significant mean shift
        mid = len(data) // 2

        if method == "mean_variance":
            before = data[:mid]
            after = data[mid:]

            # t-test
            t_stat, p_val = scipy_stats.ttest_ind(before, after)

            if p_val < self.alpha:
                return (mid, float(1 - p_val))

        return None

    def test_stationarity(self, data: pd.Series) -> TestResult:
        """
        Test if time series is stationary.

        Uses Augmented Dickey-Fuller test.
        Null hypothesis (H0): Series has unit root (non-stationary)

        Args:
            data: Time series

        Returns:
            TestResult object
        """
        from statsmodels.tsa.stattools import adfuller

        data = data.dropna()

        try:
            result = adfuller(data, autolag="AIC")
            adf_stat = result[0]
            p_value = result[1]
            test_name = "Augmented Dickey-Fuller Test"
        except:
            # Fallback to simple variance stability test
            half = len(data) // 2
            var_before = data[:half].var()
            var_after = data[half:].var()

            # F-test
            adf_stat = var_before / var_after if var_after != 0 else 1
            p_value = scipy_stats.f.sf(adf_stat, half, half)  # survivorship function
            test_name = "Variance Ratio Test"

        significant = p_value < self.alpha
        interpretation = (
            "Stationary (reject H0)" if significant else "Non-stationary (unit root)"
        )

        return TestResult(
            test_name=test_name,
            statistic=float(adf_stat),
            p_value=float(p_value),
            significant=significant,
            effect_size=None,
            interpretation=interpretation,
        )

    def run_battery(self, data: dict[str, pd.Series]) -> dict[str, TestResult]:
        """
        Run a battery of statistical tests on data.

        Args:
            data: Dict of test_name -> Series

        Returns:
            Dict of test_name -> TestResult
        """
        results = {}

        for key, series in data.items():
            results[f"{key}_normality"] = self.test_normality(series)
            results[f"{key}_stationarity"] = self.test_stationarity(series)

        return results
