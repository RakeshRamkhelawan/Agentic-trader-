"use client";

import { useHistory } from "@/lib/hooks/use-history";
import { formatCurrency, formatQuantity, cn } from "@/lib/utils";
import { format } from "date-fns";

interface TradeHistoryProps {
    className?: string;
    limit?: number;
}

export function TradeHistory({ className, limit = 10 }: TradeHistoryProps) {
    const { data: trades, isLoading } = useHistory();

    const displayTrades = (trades || []).slice(0, limit);

    if (isLoading) {
        return (
            <div className={cn("flex items-center justify-center p-4 text-xs text-muted-foreground", className)}>
                Loading history...
            </div>
        );
    }

    if (!trades || trades.length === 0) {
        return (
            <div className={cn("flex items-center justify-center p-4 text-xs text-muted-foreground", className)}>
                No recent trades
            </div>
        );
    }

    return (
        <div className={cn("flex flex-col h-full overflow-hidden", className)}>
            <div className="grid grid-cols-4 border-b border-white/5 bg-white/5 px-3 py-2 text-xs font-medium text-muted-foreground">
                <div>Time</div>
                <div>Side</div>
                <div className="text-right">Price</div>
                <div className="text-right">Size</div>
            </div>

            <div className="flex-1 overflow-auto">
                {displayTrades.map((trade) => (
                    <div
                        key={trade.id}
                        className="grid grid-cols-4 items-center px-3 py-1.5 text-xs hover:bg-white/5 transition-colors border-b border-white/5 last:border-0"
                    >
                        <div className="text-muted-foreground">
                            {format(new Date(trade.time), "HH:mm:ss")}
                        </div>
                        <div className={cn(
                            "font-medium uppercase",
                            trade.side === "buy" ? "text-brand-green" : "text-brand-red"
                        )}>
                            {trade.side}
                        </div>
                        <div className="text-right font-mono text-foreground/90">
                            {formatCurrency(trade.price).replace("€", "")}
                        </div>
                        <div className="text-right font-mono text-muted-foreground">
                            {formatQuantity(trade.amount)}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
