"use client";

import { useRef, useMemo, useState } from "react";
import { cn, formatPrice, formatQuantity } from "@/lib/utils";
import { useOrderbook, type OrderBookLevel } from "@/lib/hooks/use-orderbook";

interface OrderBookProps {
    symbol: string;
    className?: string;
    useMockData?: boolean;
}

// Generate mock orderbook data for fallback
const generateMockLevels = (
    basePrice: number,
    isAsk: boolean,
    count: number = 25
): OrderBookLevel[] => {
    const levels: OrderBookLevel[] = [];
    let cumulative = 0;

    for (let i = 0; i < count; i++) {
        const offset = (i + 1) * (Math.random() * 5 + 2);
        const price = isAsk ? basePrice + offset : basePrice - offset;
        const size = Math.random() * 2 + 0.1;
        cumulative += size;

        levels.push({
            price,
            size,
            total: cumulative,
        });
    }

    return levels;
};

export function OrderBook({
    symbol,
    className,
    useMockData = true,
}: OrderBookProps) {
    const basePrice = 45230.5;

    // Use real WebSocket data when available
    const {
        bids: wsBids,
        asks: wsAsks,
        spread: wsSpread,
        isConnected,
    } = useOrderbook(symbol);

    // Mock data as fallback
    const mockAsks = useMemo(() => generateMockLevels(basePrice, true), []);
    const mockBids = useMemo(() => generateMockLevels(basePrice, false), []);

    // Use WebSocket data if connected and not forcing mock, otherwise use mock
    const useRealData = isConnected && wsBids.length > 0 && !useMockData;
    const asks = useRealData ? wsAsks : mockAsks;
    const bids = useRealData ? wsBids : mockBids;
    const spread = useRealData ? wsSpread : asks[0]?.price - bids[0]?.price || 0;

    const maxTotal = Math.max(
        asks[asks.length - 1]?.total || 0,
        bids[bids.length - 1]?.total || 0
    );

    const spreadPercent = (spread / (bids[0]?.price || basePrice)) * 100;

    const parentRef = useRef<HTMLDivElement>(null);

    return (
        <div className={cn("flex h-full flex-col bg-card", className)}>
            {/* Header */}
            <div className="grid grid-cols-3 border-b border-border px-3 py-2 text-xs font-medium text-muted-foreground">
                <div className="flex items-center gap-1">
                    Price (EUR)
                    {/* Connection indicator */}
                    <span
                        className={cn(
                            "h-1.5 w-1.5 rounded-full",
                            isConnected ? "bg-brand-green" : "bg-muted"
                        )}
                        title={isConnected ? "Connected" : "Using mock data"}
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
                    <div className="sticky top-1/2 z-10 flex items-center justify-between border-y border-border bg-secondary px-3 py-1.5 text-xs">
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
