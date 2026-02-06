"use client";

import { useRef, useMemo } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { cn, formatPrice, formatQuantity } from "@/lib/utils";

interface OrderLevel {
    price: number;
    size: number;
    total: number;
}

interface OrderBookProps {
    symbol: string;
    className?: string;
}

// Generate mock orderbook data
const generateMockLevels = (
    basePrice: number,
    isAsk: boolean,
    count: number = 25
): OrderLevel[] => {
    const levels: OrderLevel[] = [];
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

export function OrderBook({ symbol, className }: OrderBookProps) {
    const basePrice = 45230.5;
    const asks = useMemo(() => generateMockLevels(basePrice, true), []);
    const bids = useMemo(() => generateMockLevels(basePrice, false), []);

    const maxTotal = Math.max(
        asks[asks.length - 1]?.total || 0,
        bids[bids.length - 1]?.total || 0
    );

    const spread = asks[0]?.price - bids[0]?.price || 0;
    const spreadPercent = (spread / basePrice) * 100;

    const parentRef = useRef<HTMLDivElement>(null);

    const askVirtualizer = useVirtualizer({
        count: asks.length,
        getScrollElement: () => parentRef.current,
        estimateSize: () => 24,
        overscan: 5,
    });

    const bidVirtualizer = useVirtualizer({
        count: bids.length,
        getScrollElement: () => parentRef.current,
        estimateSize: () => 24,
        overscan: 5,
    });

    return (
        <div className={cn("flex h-full flex-col bg-card", className)}>
            {/* Header */}
            <div className="grid grid-cols-3 border-b border-border px-3 py-2 text-xs font-medium text-muted-foreground">
                <div>Price (EUR)</div>
                <div className="text-right">Size</div>
                <div className="text-right">Total</div>
            </div>

            {/* Asks (sells) - reversed order */}
            <div className="flex-1 overflow-hidden">
                <div ref={parentRef} className="h-full overflow-auto">
                    {/* Asks */}
                    <div className="relative">
                        {asks
                            .slice()
                            .reverse()
                            .map((level, idx) => (
                                <OrderRow
                                    key={`ask-${idx}`}
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
                                key={`bid-${idx}`}
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
    level: OrderLevel;
    type: "bid" | "ask";
    maxTotal: number;
}

function OrderRow({ level, type, maxTotal }: OrderRowProps) {
    const depthPercent = (level.total / maxTotal) * 100;

    return (
        <div className="relative grid grid-cols-3 px-3 py-1 text-sm hover:bg-accent/50">
            {/* Depth bar background */}
            <div
                className={cn(
                    "absolute inset-y-0 right-0 opacity-20",
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
