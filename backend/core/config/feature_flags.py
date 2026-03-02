"""
Feature Flags for Gradual Rollout.

Week 1 of Exchange Integration Refactor.

Enables safe transition from old to new components.
"""

from pydantic_settings import BaseSettings


class FeatureFlags(BaseSettings):
    """
    Feature flags for safe rollout of new features.

    All flags default to False (old behavior).
    Enable gradually after testing each component.

    Example:
        >>> from backend.core.config.feature_flags import feature_flags
        >>> if feature_flags.USE_UNIFIED_SCHEMA:
        ...     order = UnifiedOrderRequest(...)
        ... else:
        ...     order = LegacyOrderRequest(...)
    """

    # Week 1: Unified Schema
    USE_UNIFIED_SCHEMA: bool = False
    """Use UnifiedOrderRequest instead of legacy schemas."""

    USE_PORTFOLIO_MANAGER_AGENT: bool = False
    """Use PortfolioManagerAgent instead of ShadowPortfolio."""

    # Week 2: Risk Integration
    USE_ENHANCED_RISK_VALIDATOR: bool = False
    """Use OrderRiskValidator in RiskManagerAgent."""

    # Week 3: TriadService Migration
    USE_REFACTORED_TRIAD_SERVICE: bool = False
    """Use refactored TriadService with OrderExecutor."""

    # Week 4: Full Migration
    USE_DECIMAL_PRECISION: bool = False
    """Use Decimal instead of float for financial values."""

    class Config:
        env_prefix = "FEATURE_"
        case_sensitive = False


# Global instance
feature_flags = FeatureFlags()


def is_enabled(flag_name: str) -> bool:
    """
    Check if a feature flag is enabled.

    Args:
        flag_name: Name of the flag (e.g., "USE_UNIFIED_SCHEMA")

    Returns:
        True if flag is enabled
    """
    return getattr(feature_flags, flag_name, False)
