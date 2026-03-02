"""Data provider for admin dashboards."""

from datetime import datetime, timedelta
from typing import Any

from backend.tenancy.tenant_manager import TenantStatus, tenant_manager


class DashboardDataProvider:
    """
    Provides aggregated data for admin dashboards.

    Generates:
    - Time-series metrics
    - Growth statistics
    - Usage trends
    - Alert summaries
    """

    def __init__(self):
        pass

    def get_growth_metrics(self, days: int = 30) -> dict[str, Any]:
        """Get tenant growth metrics."""
        # In production, query time-series database
        # For now, generate sample data

        dates = []
        new_tenants = []
        active_tenants = []

        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days - i - 1)
            dates.append(date.strftime("%Y-%m-%d"))

            # Sample data
            new_tenants.append(max(0, (i % 7) - 2))
            active_tenants.append(50 + i)

        return {
            "period": f"last_{days}_days",
            "dates": dates,
            "metrics": {
                "new_tenants": new_tenants,
                "active_tenants": active_tenants,
                "cumulative": self._calculate_cumulative(new_tenants),
            },
        }

    def _calculate_cumulative(self, daily_values: list[int]) -> list[int]:
        """Calculate cumulative values."""
        cumulative = []
        total = 0
        for value in daily_values:
            total += value
            cumulative.append(total)
        return cumulative

    def get_usage_metrics(self) -> dict[str, Any]:
        """Get platform-wide usage metrics."""
        tenants = tenant_manager.list_tenants()

        total_api_calls = 0
        total_trades = 0
        total_users = 0

        for tenant in tenants:
            usage = tenant_manager.get_usage(tenant.id)
            total_api_calls += usage.get("current_usage", {}).get("api_calls", 0)
            total_trades += usage.get("current_usage", {}).get("trades", 0)
            total_users += usage.get("current_usage", {}).get("users", 0)

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "totals": {
                "api_calls": total_api_calls,
                "trades": total_trades,
                "users": total_users,
                "tenants": len(tenants),
            },
            "averages_per_tenant": {
                "api_calls": total_api_calls / len(tenants) if tenants else 0,
                "trades": total_trades / len(tenants) if tenants else 0,
                "users": total_users / len(tenants) if tenants else 0,
            },
        }

    def get_alerts(self) -> list[dict[str, Any]]:
        """Get system alerts for admin attention."""
        alerts = []

        # Check for suspended tenants
        suspended = tenant_manager.list_tenants(status=TenantStatus.SUSPENDED)
        if suspended:
            alerts.append({
                "level": "warning",
                "category": "billing",
                "message": f"{len(suspended)} tenant(s) suspended",
                "action": "Review suspended accounts",
            })

        # Check for pending activations
        pending = tenant_manager.list_tenants(status=TenantStatus.PENDING)
        if len(pending) > 5:
            alerts.append({
                "level": "info",
                "category": "onboarding",
                "message": f"{len(pending)} tenant(s) awaiting activation",
                "action": "Process pending activations",
            })

        # Check for high usage (sample check)
        # In production, query actual usage metrics

        return alerts

    def get_top_tenants(self, metric: str = "users", limit: int = 10) -> list[dict[str, Any]]:
        """Get top tenants by metric."""
        tenants = tenant_manager.list_tenants(status=TenantStatus.ACTIVE)

        # Get usage for each tenant
        tenant_data = []
        for tenant in tenants:
            usage = tenant_manager.get_usage(tenant.id)
            current = usage.get("current_usage", {})

            value = current.get(metric, 0)
            tenant_data.append({
                "tenant_id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "tier": tenant.tier.value,
                "value": value,
            })

        # Sort by value descending
        tenant_data.sort(key=lambda x: x["value"], reverse=True)

        return tenant_data[:limit]

    def get_churn_risk_tenants(self) -> list[dict[str, Any]]:
        """Identify tenants at risk of churning."""
        # In production, use ML model or heuristics
        # For now, return empty list
        return []

    def get_recent_activity(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent platform activity."""
        # In production, query activity log
        return []


class ChartDataProvider:
    """Provides data formatted for charts/graphs."""

    @staticmethod
    def get_tenant_distribution_by_tier() -> dict[str, Any]:
        """Get tenant distribution data for pie chart."""
        stats = tenant_manager.get_stats()
        by_tier = stats.get("by_tier", {})

        return {
            "type": "pie",
            "labels": list(by_tier.keys()),
            "data": list(by_tier.values()),
        }

    @staticmethod
    def get_mrr_trend(days: int = 90) -> dict[str, Any]:
        """Get MRR trend data for line chart."""
        dates = []
        mrr_values = []

        # Sample data - in production query actual billing data
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days - i - 1)
            dates.append(date.strftime("%Y-%m-%d"))
            mrr_values.append(10000 + (i * 100))  # Growing MRR

        return {
            "type": "line",
            "labels": dates,
            "datasets": [
                {
                    "label": "Monthly Recurring Revenue",
                    "data": mrr_values,
                }
            ],
        }

    @staticmethod
    def get_api_usage_heatmap() -> dict[str, Any]:
        """Get API usage heatmap data."""
        # 7 days x 24 hours
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        hours = [f"{h:02d}:00" for h in range(24)]

        # Sample heatmap data
        data = []
        for day in range(7):
            for hour in range(24):
                # Higher usage during business hours
                base = 50 if 9 <= hour <= 17 else 10
                value = base + (day * 5)
                data.append({
                    "day": day,
                    "hour": hour,
                    "value": value,
                })

        return {
            "type": "heatmap",
            "days": days,
            "hours": hours,
            "data": data,
        }
