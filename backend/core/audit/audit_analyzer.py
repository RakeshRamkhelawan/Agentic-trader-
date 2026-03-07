"""
Audit Log Analyzer - Analyze trading decisions and agent performance
"""

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


class AuditAnalyzer:
    """Analyze audit logs for insights"""

    def __init__(self, audit_file: str):
        with open(audit_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.session_info = self.data["session_info"]
        self.agent_decisions = self.data["agent_decisions"]
        self.collective_decisions = self.data["collective_deliberations"]
        self.risk_checks = self.data["risk_checks"]
        self.sizing_logs = self.data["position_sizing"]
        self.executions = self.data["trade_executions"]
        self.exits = self.data["trade_exits"]

    def generate_report(self) -> str:
        """Generate comprehensive text report"""
        lines = []
        lines.append("=" * 80)
        lines.append("  AUDIT LOG ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(f"  Session: {self.session_info['session_id']}")
        lines.append(f"  Period:  {self.session_info['start_time']}")
        lines.append("")

        # Agent Performance
        lines.append("  AGENT PERFORMANCE")
        lines.append("-" * 80)
        agent_stats = self._analyze_agents()
        for agent, stats in sorted(agent_stats.items()):
            lines.append(
                f"  {agent:20s} | Signals: {stats['count']:5d} | "
                f"Avg Conf: {stats['avg_confidence']:.3f} | "
                f"Guna: {stats['dominant_guna']}"
            )
        lines.append("")

        # Collective Decision Analysis
        lines.append("  COLLECTIVE DECISION ANALYSIS")
        lines.append("-" * 80)
        coll_stats = self._analyze_collective()
        lines.append(f"  Total Deliberations:    {coll_stats['total']}")
        lines.append(f"  Avg Harmony Score:      {coll_stats['avg_harmony']:.3f}")
        lines.append(f"  Avg Coherence:          {coll_stats['avg_coherence']:.3f}")
        lines.append(
            f"  Maya Detections:        {coll_stats['maya_count']} ({coll_stats['maya_rate']:.1%})"
        )
        lines.append(f"  Dominant Elements:      {dict(coll_stats['elements'])}")
        lines.append(f"  Dominant Gunas:         {dict(coll_stats['gunas'])}")
        lines.append("")

        # Risk Analysis
        lines.append("  RISK MANAGEMENT ANALYSIS")
        lines.append("-" * 80)
        risk_stats = self._analyze_risk()
        lines.append(f"  Total Checks:           {risk_stats['total']}")
        lines.append(
            f"  Passed:                 {risk_stats['passed']} ({risk_stats['pass_rate']:.1%})"
        )
        lines.append(
            f"  Rejected:               {risk_stats['rejected']} ({risk_stats['reject_rate']:.1%})"
        )
        lines.append("  Top Rejection Reasons:")
        for reason, count in risk_stats["rejection_reasons"][:5]:
            lines.append(f"    - {reason}: {count}")
        lines.append("")

        # Trade Performance
        lines.append("  TRADE PERFORMANCE")
        lines.append("-" * 80)
        trade_stats = self._analyze_trades()
        lines.append(f"  Total Trades:           {trade_stats['total']}")
        lines.append(f"  Completed:              {len(self.exits)}")
        lines.append(f"  Avg Entry Size:         ${trade_stats['avg_size']:,.2f}")
        lines.append(f"  Avg Confidence:         {trade_stats['avg_confidence']:.3f}")
        lines.append(f"  Avg Harmony at Entry:   {trade_stats['avg_harmony']:.3f}")
        lines.append("  Symbol Distribution:")
        for sym, count in list(trade_stats["symbols"].items())[:10]:
            lines.append(f"    - {sym}: {count}")
        lines.append("")

        # Exit Analysis
        if self.exits:
            lines.append("  EXIT ANALYSIS")
            lines.append("-" * 80)
            exit_stats = self._analyze_exits()
            lines.append(f"  Total Exits:            {exit_stats['total']}")
            lines.append(f"  Win Rate:               {exit_stats['win_rate']:.1%}")
            lines.append(f"  Avg PnL:                ${exit_stats['avg_pnl']:,.2f}")
            lines.append(f"  Total PnL:              ${exit_stats['total_pnl']:,.2f}")
            lines.append("  Exit Reasons:")
            for reason, count in exit_stats["reasons"].items():
                lines.append(f"    - {reason}: {count}")
            lines.append(f"  Avg Hold Time:          {exit_stats['avg_bars']:.1f} bars")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _analyze_agents(self) -> Dict[str, Dict]:
        """Analyze individual agent performance"""
        stats = defaultdict(
            lambda: {
                "count": 0,
                "confidences": [],
                "strengths": [],
                "guna_counts": defaultdict(int),
            }
        )

        for decision in self.agent_decisions:
            agent = decision["agent_name"]
            stats[agent]["count"] += 1
            stats[agent]["confidences"].append(decision["confidence"])
            stats[agent]["strengths"].append(decision["strength"])

            # Track guna
            guna = decision.get("guna_state", {})
            if guna:
                dominant = max(guna, key=guna.get)
                stats[agent]["guna_counts"][dominant] += 1

        # Calculate averages
        result = {}
        for agent, data in stats.items():
            result[agent] = {
                "count": data["count"],
                "avg_confidence": statistics.mean(data["confidences"]),
                "avg_strength": statistics.mean(data["strengths"]),
                "dominant_guna": (
                    max(data["guna_counts"], key=data["guna_counts"].get)
                    if data["guna_counts"]
                    else "unknown"
                ),
            }

        return result

    def _analyze_collective(self) -> Dict[str, Any]:
        """Analyze collective decisions"""
        harmonies = []
        coherences = []
        maya_count = 0
        elements = defaultdict(int)
        gunas = defaultdict(int)

        for decision in self.collective_decisions:
            harmonies.append(decision["harmony_score"])
            coherences.append(decision["coherence"])
            if decision["is_maya"]:
                maya_count += 1
            elements[decision["dominant_element"]] += 1
            gunas[decision["guna_dominant"]] += 1

        return {
            "total": len(self.collective_decisions),
            "avg_harmony": statistics.mean(harmonies) if harmonies else 0,
            "avg_coherence": statistics.mean(coherences) if coherences else 0,
            "maya_count": maya_count,
            "maya_rate": maya_count / max(1, len(self.collective_decisions)),
            "elements": dict(elements),
            "gunas": dict(gunas),
        }

    def _analyze_risk(self) -> Dict[str, Any]:
        """Analyze risk checks"""
        passed = sum(1 for r in self.risk_checks if r["passed"])
        rejected = len(self.risk_checks) - passed

        rejection_reasons = defaultdict(int)
        for check in self.risk_checks:
            if not check["passed"] and check["rejection_reason"]:
                rejection_reasons[check["rejection_reason"]] += 1

        return {
            "total": len(self.risk_checks),
            "passed": passed,
            "rejected": rejected,
            "pass_rate": passed / max(1, len(self.risk_checks)),
            "reject_rate": rejected / max(1, len(self.risk_checks)),
            "rejection_reasons": sorted(rejection_reasons.items(), key=lambda x: -x[1]),
        }

    def _analyze_trades(self) -> Dict[str, Any]:
        """Analyze executed trades"""
        sizes = []
        confidences = []
        harmonies = []
        symbols = defaultdict(int)

        for trade in self.executions:
            sizes.append(trade["size"])
            symbols[trade["symbol"]] += 1

        # Get confidence/harmony from collective decisions
        for decision in self.collective_decisions:
            confidences.append(decision["final_confidence"])
            harmonies.append(decision["harmony_score"])

        return {
            "total": len(self.executions),
            "avg_size": statistics.mean(sizes) if sizes else 0,
            "avg_confidence": statistics.mean(confidences) if confidences else 0,
            "avg_harmony": statistics.mean(harmonies) if harmonies else 0,
            "symbols": dict(sorted(symbols.items(), key=lambda x: -x[1])),
        }

    def _analyze_exits(self) -> Dict[str, Any]:
        """Analyze trade exits"""
        pnls = [e["net_pnl"] for e in self.exits]
        wins = sum(1 for p in pnls if p > 0)
        reasons = defaultdict(int)
        bars = [e["bars_held"] for e in self.exits]

        for exit in self.exits:
            reasons[exit["exit_reason"]] += 1

        return {
            "total": len(self.exits),
            "win_rate": wins / max(1, len(self.exits)),
            "avg_pnl": statistics.mean(pnls) if pnls else 0,
            "total_pnl": sum(pnls),
            "reasons": dict(reasons),
            "avg_bars": statistics.mean(bars) if bars else 0,
        }


def main():
    """CLI for audit analysis"""
    import sys

    if len(sys.argv) < 2:
        # Find latest audit file
        audit_dir = Path("backend/data/audit_logs")
        files = sorted(audit_dir.glob("audit_*.json"))
        if not files:
            print("No audit files found")
            return
        audit_file = files[-1]
    else:
        audit_file = sys.argv[1]

    print(f"Analyzing: {audit_file}")
    analyzer = AuditAnalyzer(audit_file)
    print(analyzer.generate_report())


if __name__ == "__main__":
    main()
