"use client";

import { useRef, useState } from "react";
import { cn, formatPrice, formatQuantity } from "@/lib/utils";
import { useOrderbook, type OrderBookLevel } from "@/lib/hooks/use-orderbook";

interface OrderBookProps {
    symbol: string;
    className?: string;
}

// Mock data generation removed for GTM production implementation

export function OrderBook({
    symbol,
    className,
}: OrderBookProps) {
    // Use real WebSocket data
    const {
        bids,
        asks,
        spread,
        isConnected,
    } = useOrderbook(symbol);

    const maxTotal = Math.max(
        asks[asks.length - 1]?.total || 0,
        bids[bids.length - 1]?.total || 0
    );

    const bestBid = bids[0]?.price || 0;
    const spreadPercent = bestBid > 0 ? (spread / bestBid) * 100 : 0;

    const parentRef = useRef<HTMLDivElement>(null);

    // Empty state if connected but no data
    if (isConnected && bids.length === 0 && asks.length === 0) {
        return (
            <div className={cn("flex h-full flex-col bg-card items-center justify-center p-4", className)}>
                <div className="text-center space-y-2">
                    <div className="text-muted-foreground text-sm">Waiting for order book...</div>
                    <div className="text-xs text-muted-foreground/50">Market: {symbol}</div>
                </div>
            </div>
        );
    }

    return (
        <div className={cn("flex h-full flex-col", className)}>
            {/* Header */}
            <div className="grid grid-cols-3 border-b border-white/5 bg-white/5 px-3 py-2 text-xs font-medium text-muted-foreground">
                <div className="flex items-center gap-1">
                    Price (EUR)
                    {/* Connection indicator */}
                    <span
                        className={cn(
                            "h-1.5 w-1.5 rounded-full",
                            isConnected ? "bg-brand-green" : "bg-brand-red"
                        )}
                        title={isConnected ? "Connected" : "Disconnected"}
                    />
                </div>
                <div className="text-right">Size</div>
                <div className="text-right">Total</div>
            </div>

            {/* OrderBook content */}
            <div className="flex-1 overflow-hidden">
                <div ref={parentRef} className="h-full overflow-auto">
                    {/* Asks - reversed order so best ask is at bottom */}
                    <div className="relative">
                        {asks
                            .slice()
                            .reverse()
                            .map((level, idx) => (
                                <OrderRow
                                    key={`ask-${level.price}-${idx}`}
                                    level={level}
                                    type="ask"
                                    maxTotal={maxTotal}
                                />
                            ))}
                    </div>

                    {/* Spread */}
                    <div className="sticky top-1/2 z-10 flex items-center justify-between border-y border-white/5 bg-black/20 backdrop-blur-sm px-3 py-1.5 text-xs">
                        <span className="text-muted-foreground">Spread</span>
                        <span className="font-mono font-medium">
                            {formatPrice(spread)} ({spreadPercent.toFixed(3)}%)
                        </span>
                    </div>

                    {/* Bids */}
                    <div className="relative">
                        {bids.map((level, idx) => (
                            <OrderRow
                                key={`bid-${level.price}-${idx}`}
                                level={level}
                                type="bid"
                                maxTotal={maxTotal}
                            />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

interface OrderRowProps {
    level: OrderBookLevel;
    type: "bid" | "ask";
    maxTotal: number;
}

function OrderRow({ level, type, maxTotal }: OrderRowProps) {
    const depthPercent = (level.total / maxTotal) * 100;
    const [flash, setFlash] = useState(false);

    // Flash animation when price updates could be added here
    // with useEffect watching level.size changes

    return (
        <div
            className={cn(
                "relative grid grid-cols-3 px-3 py-1 text-sm transition-colors hover:bg-accent/50",
                flash && (type === "bid" ? "animate-price-up" : "animate-price-down")
            )}
        >
            {/* Depth bar background */}
            <div
                className={cn(
                    "absolute inset-y-0 right-0 opacity-20 transition-all duration-300",
                    type === "bid" ? "bg-brand-green" : "bg-brand-red"
                )}
                style={{ width: `${depthPercent}%` }}
            />

            {/* Content */}
            <div
                className={cn(
                    "relative z-10 font-mono",
                    type === "bid" ? "text-brand-green" : "text-brand-red"
                )}
            >
                {formatPrice(level.price)}
            </div>
            <div className="relative z-10 text-right font-mono">
                {formatQuantity(level.size)}
            </div>
            <div className="relative z-10 text-right font-mono text-muted-foreground">
                {formatQuantity(level.total)}
            </div>
        </div>
    );
}
