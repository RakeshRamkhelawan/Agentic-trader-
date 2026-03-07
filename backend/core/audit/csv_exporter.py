"""
Audit Log CSV Exporter
Converts JSON audit logs to CSV files for Excel analysis
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


class AuditCSVExporter:
    """Export audit logs to CSV format"""

    def __init__(self, audit_file: str, output_dir: str = "backend/data/audit_csv"):
        self.audit_file = Path(audit_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        with open(audit_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def export_all(self) -> Dict[str, Path]:
        """Export all audit data to separate CSV files"""
        files = {}

        files["agent_decisions"] = self.export_agent_decisions()
        files["collective_deliberations"] = self.export_collective_decisions()
        files["risk_checks"] = self.export_risk_checks()
        files["position_sizing"] = self.export_position_sizing()
        files["trade_executions"] = self.export_trade_executions()
        files["trade_exits"] = self.export_trade_exits()
        files["summary"] = self.export_summary()

        return files

    def export_agent_decisions(self) -> Path:
        """Export agent decisions to CSV"""
        output_file = self.output_dir / "agent_decisions.csv"

        fieldnames = [
            "timestamp",
            "agent_name",
            "agent_element",
            "symbol",
            "action",
            "confidence",
            "strength",
            "reasoning",
            "prana_level",
            "guna_sattva",
            "guna_rajas",
            "guna_tamas",
        ]

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for decision in self.data["agent_decisions"]:
                row = {
                    "timestamp": decision["timestamp"],
                    "agent_name": decision["agent_name"],
                    "agent_element": decision["agent_element"],
                    "symbol": decision["symbol"],
                    "action": decision["action"],
                    "confidence": decision["confidence"],
                    "strength": decision["strength"],
                    "reasoning": decision["reasoning"],
                    "prana_level": decision.get("prana_level", 0),
                    "guna_sattva": decision.get("guna_state", {}).get("sattva", 0),
                    "guna_rajas": decision.get("guna_state", {}).get("rajas", 0),
                    "guna_tamas": decision.get("guna_state", {}).get("tamas", 0),
                }
                writer.writerow(row)

        print(f"  Exported {len(self.data['agent_decisions'])} agent decisions to {output_file}")
        return output_file

    def export_collective_decisions(self) -> Path:
        """Export collective deliberations to CSV"""
        output_file = self.output_dir / "collective_deliberations.csv"

        fieldnames = [
            "timestamp",
            "session_id",
            "symbol",
            "final_action",
            "final_confidence",
            "coherence",
            "harmony_score",
            "weighted_strength",
            "dominant_element",
            "suppressed_element",
            "guna_dominant",
            "guna_sattva",
            "guna_rajas",
            "guna_tamas",
            "is_maya",
            "maya_score",
            "maya_reason",
            "participating_agents",
        ]

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for decision in self.data["collective_deliberations"]:
                guna_state = decision.get("collective_guna", {})
                row = {
                    "timestamp": decision["timestamp"],
                    "session_id": decision["session_id"],
                    "symbol": decision["symbol"],
                    "final_action": decision["final_action"],
                    "final_confidence": decision["final_confidence"],
                    "coherence": decision["coherence"],
                    "harmony_score": decision["harmony_score"],
                    "weighted_strength": decision["weighted_strength"],
                    "dominant_element": decision["dominant_element"],
                    "suppressed_element": decision.get("suppressed_element", ""),
                    "guna_dominant": decision["guna_dominant"],
                    "guna_sattva": guna_state.get("sattva", 0),
                    "guna_rajas": guna_state.get("rajas", 0),
                    "guna_tamas": guna_state.get("tamas", 0),
                    "is_maya": decision["is_maya"],
                    "maya_score": decision["maya_score"],
                    "maya_reason": decision["maya_reason"],
                    "participating_agents": "|".join(decision["participating_agents"]),
                }
                writer.writerow(row)

        print(
            f"  Exported {len(self.data['collective_deliberations'])} collective decisions to {output_file}"
        )
        return output_file

    def export_risk_checks(self) -> Path:
        """Export risk checks to CSV"""
        output_file = self.output_dir / "risk_checks.csv"

        fieldnames = [
            "timestamp",
            "session_id",
            "symbol",
            "sector",
            "passed",
            "rejection_reason",
            "harmony_check",
            "harmony_score",
            "maya_check",
            "drawdown_check",
            "current_drawdown",
            "position_limit_check",
            "active_positions",
            "sector_exposure",
        ]

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for check in self.data["risk_checks"]:
                row = {
                    "timestamp": check["timestamp"],
                    "session_id": check["session_id"],
                    "symbol": check["symbol"],
                    "sector": check["sector"],
                    "passed": check["passed"],
                    "rejection_reason": check.get("rejection_reason", ""),
                    "harmony_check": check["harmony_check"],
                    "harmony_score": check["harmony_score"],
                    "maya_check": check["maya_check"],
                    "drawdown_check": check["drawdown_check"],
                    "current_drawdown": check["current_drawdown"],
                    "position_limit_check": check["position_limit_check"],
                    "active_positions": check["active_positions"],
                    "sector_exposure": check["sector_exposure"],
                }
                writer.writerow(row)

        print(f"  Exported {len(self.data['risk_checks'])} risk checks to {output_file}")
        return output_file

    def export_position_sizing(self) -> Path:
        """Export position sizing calculations to CSV"""
        output_file = self.output_dir / "position_sizing.csv"

        fieldnames = [
            "timestamp",
            "session_id",
            "symbol",
            "capital",
            "base_risk",
            "confidence",
            "harmony",
            "guna_dominant",
            "atr",
            "price",
            "calculated_size",
            "max_position",
            "final_size",
            "confidence_mult",
            "harmony_mult",
            "guna_mult",
            "strategic_mult",
        ]

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for sizing in self.data["position_sizing"]:
                row = {
                    "timestamp": sizing["timestamp"],
                    "session_id": sizing["session_id"],
                    "symbol": sizing["symbol"],
                    "capital": sizing["capital"],
                    "base_risk": sizing["base_risk"],
                    "confidence": sizing["confidence"],
                    "harmony": sizing["harmony"],
                    "guna_dominant": sizing["guna_dominant"],
                    "atr": sizing["atr"],
                    "price": sizing["price"],
                    "calculated_size": sizing["calculated_size"],
                    "max_position": sizing["max_position"],
                    "final_size": sizing["final_size"],
                    "confidence_mult": sizing["confidence_mult"],
                    "harmony_mult": sizing["harmony_mult"],
                    "guna_mult": sizing["guna_mult"],
                    "strategic_mult": sizing["strategic_mult"],
                }
                writer.writerow(row)

        print(
            f"  Exported {len(self.data['position_sizing'])} sizing calculations to {output_file}"
        )
        return output_file

    def export_trade_executions(self) -> Path:
        """Export trade executions to CSV"""
        output_file = self.output_dir / "trade_executions.csv"

        fieldnames = [
            "timestamp",
            "session_id",
            "trade_id",
            "symbol",
            "side",
            "size",
            "price",
            "atr",
            "stop_price",
            "tp_price",
            "trailing_mult",
            "transaction_cost",
            "slippage_cost",
            "total_cost",
            "market_regime",
            "trend_1d",
            "adx",
            "rsi",
            "collective_decision_id",
        ]

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for trade in self.data["trade_executions"]:
                row = {
                    "timestamp": trade["timestamp"],
                    "session_id": trade["session_id"],
                    "trade_id": trade["trade_id"],
                    "symbol": trade["symbol"],
                    "side": trade["side"],
                    "size": trade["size"],
                    "price": trade["price"],
                    "atr": trade["atr"],
                    "stop_price": trade["stop_price"],
                    "tp_price": trade["tp_price"],
                    "trailing_mult": trade["trailing_mult"],
                    "transaction_cost": trade["transaction_cost"],
                    "slippage_cost": trade["slippage_cost"],
                    "total_cost": trade["total_cost"],
                    "market_regime": trade["market_regime"],
                    "trend_1d": trade["trend_1d"],
                    "adx": trade["adx"],
                    "rsi": trade["rsi"],
                    "collective_decision_id": trade["collective_decision_id"],
                }
                writer.writerow(row)

        print(f"  Exported {len(self.data['trade_executions'])} trade executions to {output_file}")
        return output_file

    def export_trade_exits(self) -> Path:
        """Export trade exits to CSV"""
        output_file = self.output_dir / "trade_exits.csv"

        fieldnames = [
            "timestamp",
            "trade_id",
            "symbol",
            "exit_price",
            "exit_reason",
            "bars_held",
            "gross_pnl",
            "exit_costs",
            "net_pnl",
            "return_pct",
            "entry_harmony",
        ]

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for exit in self.data["trade_exits"]:
                row = {
                    "timestamp": exit["timestamp"],
                    "trade_id": exit["trade_id"],
                    "symbol": exit["symbol"],
                    "exit_price": exit["exit_price"],
                    "exit_reason": exit["exit_reason"],
                    "bars_held": exit["bars_held"],
                    "gross_pnl": exit["gross_pnl"],
                    "exit_costs": exit["exit_costs"],
                    "net_pnl": exit["net_pnl"],
                    "return_pct": exit["return_pct"],
                    "entry_harmony": exit["entry_harmony"],
                }
                writer.writerow(row)

        print(f"  Exported {len(self.data['trade_exits'])} trade exits to {output_file}")
        return output_file

    def export_summary(self) -> Path:
        """Export session summary to CSV"""
        output_file = self.output_dir / "session_summary.csv"

        info = self.data["session_info"]

        fieldnames = ["metric", "value"]

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            summary_data = [
                {"metric": "session_id", "value": info["session_id"]},
                {"metric": "start_time", "value": info["start_time"]},
                {"metric": "end_time", "value": info["end_time"]},
                {"metric": "decision_count", "value": info["decision_count"]},
                {"metric": "trade_count", "value": info["trade_count"]},
                {"metric": "rejection_count", "value": info["rejection_count"]},
                {"metric": "agent_decisions", "value": len(self.data["agent_decisions"])},
                {
                    "metric": "collective_deliberations",
                    "value": len(self.data["collective_deliberations"]),
                },
                {"metric": "risk_checks", "value": len(self.data["risk_checks"])},
                {"metric": "position_sizing", "value": len(self.data["position_sizing"])},
                {"metric": "trade_executions", "value": len(self.data["trade_executions"])},
                {"metric": "trade_exits", "value": len(self.data["trade_exits"])},
            ]

            writer.writerows(summary_data)

        print(f"  Exported session summary to {output_file}")
        return output_file

    def create_excel_summary(self) -> Path:
        """Create a summary file for Excel pivot tables"""
        output_file = self.output_dir / "excel_pivot_data.csv"

        # Join collective decisions with trade executions
        fieldnames = [
            "symbol",
            "final_action",
            "harmony_score",
            "coherence",
            "is_maya",
            "guna_dominant",
            "dominant_element",
            "trade_executed",
            "exit_reason",
            "net_pnl",
            "bars_held",
        ]

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # Create lookup for trades by decision ID
            trade_lookup = {}
            exit_lookup = {}

            for trade in self.data["trade_executions"]:
                decision_id = trade["collective_decision_id"]
                trade_lookup[decision_id] = trade

            for exit in self.data["trade_exits"]:
                exit_lookup[exit["trade_id"]] = exit

            # Match collective decisions with trades
            for i, decision in enumerate(self.data["collective_deliberations"]):
                decision_id = f"{decision['session_id']}_{i+1}"

                if decision_id in trade_lookup:
                    trade = trade_lookup[decision_id]

                    # Find exit if exists
                    exit_data = exit_lookup.get(trade["trade_id"], {})

                    row = {
                        "symbol": decision["symbol"],
                        "final_action": decision["final_action"],
                        "harmony_score": decision["harmony_score"],
                        "coherence": decision["coherence"],
                        "is_maya": decision["is_maya"],
                        "guna_dominant": decision["guna_dominant"],
                        "dominant_element": decision["dominant_element"],
                        "trade_executed": "YES",
                        "exit_reason": exit_data.get("exit_reason", "OPEN"),
                        "net_pnl": exit_data.get("net_pnl", 0),
                        "bars_held": exit_data.get("bars_held", 0),
                    }
                    writer.writerow(row)

        print(
            f"  Created Excel pivot data ({len(self.data['trade_executions'])} rows) to {output_file}"
        )
        return output_file


def main():
    """CLI for CSV export"""
    parser = argparse.ArgumentParser(description="Export audit logs to CSV")
    parser.add_argument("audit_file", nargs="?", help="Path to audit JSON file")
    parser.add_argument("-o", "--output", default="backend/data/audit_csv", help="Output directory")
    args = parser.parse_args()

    if not args.audit_file:
        # Find latest audit file
        audit_dir = Path("backend/data/audit_logs")
        files = sorted(audit_dir.glob("audit_*.json"))
        if not files:
            print("No audit files found")
            return
        args.audit_file = files[-1]

    print(f"Exporting: {args.audit_file}")
    print("=" * 80)

    exporter = AuditCSVExporter(args.audit_file, args.output)
    files = exporter.export_all()

    # Also create Excel pivot data
    pivot_file = exporter.create_excel_summary()

    print("=" * 80)
    print(f"Export complete! Files created in: {args.output}")
    print("\nGenerated files:")
    for name, path in files.items():
        size = path.stat().st_size / 1024
        print(f"  {name:25s} {size:8.1f} KB")
    print(f"  {'excel_pivot_data':25s} {pivot_file.stat().st_size / 1024:8.1f} KB")

    print("\nTips for Excel analysis:")
    print("  1. Open excel_pivot_data.csv for trade analysis")
    print("  2. Use agent_decisions.csv for agent performance")
    print("  3. Use collective_deliberations.csv for decision quality")
    print("  4. Create pivot tables: Symbol vs Avg PnL, Harmony vs Win Rate")


if __name__ == "__main__":
    main()
