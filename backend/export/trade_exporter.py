"""Trade history export functionality."""

import csv
import json
from datetime import datetime
from io import StringIO
from typing import Any


class TradeExporter:
    """
    Exports trade history in various formats.

    Supported formats:
    - CSV
    - JSON
    - Excel (XLSX)
    """

    def __init__(self):
        self.supported_formats = ["csv", "json", "xlsx"]

    def export_trades(
        self,
        trades: list[dict[str, Any]],
        format: str = "csv",
        include_header: bool = True,
    ) -> bytes:
        """
        Export trades to specified format.

        Args:
            trades: List of trade dictionaries
            format: Export format (csv, json, xlsx)
            include_header: Include header row for CSV

        Returns:
            Exported data as bytes
        """
        format = format.lower()

        if format == "csv":
            return self._export_csv(trades, include_header)
        elif format == "json":
            return self._export_json(trades)
        elif format == "xlsx":
            return self._export_xlsx(trades)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_csv(
        self,
        trades: list[dict[str, Any]],
        include_header: bool,
    ) -> bytes:
        """Export trades to CSV format."""
        output = StringIO()
        writer = csv.writer(output)

        if include_header and trades:
            headers = self._get_csv_headers(trades[0])
            writer.writerow(headers)

        for trade in trades:
            row = self._trade_to_row(trade)
            writer.writerow(row)

        return output.getvalue().encode("utf-8")

    def _get_csv_headers(self, trade: dict[str, Any]) -> list[str]:
        """Get CSV headers from trade data."""
        field_mapping = {
            "timestamp": "Date/Time",
            "symbol": "Symbol",
            "side": "Side",
            "quantity": "Quantity",
            "entry_price": "Entry Price",
            "exit_price": "Exit Price",
            "pnl": "P&L",
            "pnl_percent": "P&L %",
            "status": "Status",
            "strategy": "Strategy",
        }

        headers = []
        for key in trade:
            headers.append(field_mapping.get(key, key.title()))

        return headers

    def _trade_to_row(self, trade: dict[str, Any]) -> list[Any]:
        """Convert trade dict to CSV row."""
        row = []
        for value in trade.values():
            if isinstance(value, datetime):
                row.append(value.isoformat())
            elif isinstance(value, float):
                row.append(f"{value:.8f}")
            else:
                row.append(value)
        return row

    def _export_json(self, trades: list[dict[str, Any]]) -> bytes:
        """Export trades to JSON format."""
        # Convert datetime objects to strings
        serializable_trades = []
        for trade in trades:
            trade_copy = trade.copy()
            for key, value in trade_copy.items():
                if isinstance(value, datetime):
                    trade_copy[key] = value.isoformat()
            serializable_trades.append(trade_copy)

        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "trade_count": len(trades),
            "trades": serializable_trades,
        }

        return json.dumps(data, indent=2).encode("utf-8")

    def _export_xlsx(self, trades: list[dict[str, Any]]) -> bytes:
        """
        Export trades to Excel format.

        Note: This is a placeholder. In production, use openpyxl or xlsxwriter.
        """
        # For now, return CSV with .xlsx extension note
        # In production, implement actual Excel export
        csv_data = self._export_csv(trades, True)
        return csv_data

    def generate_summary(
        self,
        trades: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate trade summary statistics."""
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0,
            }

        pnls = [t.get("pnl", 0) for t in trades]
        winning = [p for p in pnls if p > 0]
        losing = [p for p in pnls if p <= 0]

        return {
            "total_trades": len(trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": (len(winning) / len(trades) * 100) if trades else 0.0,
            "total_pnl": sum(pnls),
            "avg_pnl": sum(pnls) / len(trades),
            "best_trade": max(pnls),
            "worst_trade": min(pnls),
        }

    def export_with_summary(
        self,
        trades: list[dict[str, Any]],
        format: str = "csv",
    ) -> dict[str, Any]:
        """Export trades with summary statistics."""
        data = self.export_trades(trades, format)
        summary = self.generate_summary(trades)

        return {
            "data": data,
            "summary": summary,
            "format": format,
            "filename": f"trades_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format}",
        }


# Global exporter instance
trade_exporter = TradeExporter()
