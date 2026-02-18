"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { wsClient, type IncomingMessage } from "@/lib/api/websocket-client";

export interface OrderBookLevel {
    price: number;
    size: number;
    total: number;
}

interface OrderBookData {
    bids: OrderBookLevel[];
    asks: OrderBookLevel[];
    spread: number;
    isConnected: boolean;
    lastUpdate: Date | null;
}

interface RawOrderBookMessage extends IncomingMessage {
    data: {
        bids: [number, number][];
        asks: [number, number][];
    };
}

/**
 * Process raw price levels into OrderBookLevel objects with cumulative totals.
 */
function processLevels(levels: [number, number][]): OrderBookLevel[] {
    let cumulative = 0;
    return levels.map(([price, size]) => {
        cumulative += size;
        return { price, size, total: cumulative };
    });
}

/**
 * Merge delta updates into existing orderbook.
 * Removes levels with size 0, updates existing, or inserts new levels.
 */
function mergeDelta(
    current: OrderBookLevel[],
    delta: [number, number][],
    isBid: boolean
): OrderBookLevel[] {
    const priceMap = new Map<number, number>();

    // Add current levels to map
    current.forEach((level) => priceMap.set(level.price, level.size));

    // Apply delta
    delta.forEach(([price, size]) => {
        if (size === 0) {
            priceMap.delete(price);
        } else {
            priceMap.set(price, size);
        }
    });

    // Convert back to array and sort
    const sorted = Array.from(priceMap.entries())
        .map(([price, size]) => ({ price, size, total: 0 }))
        .sort((a, b) => (isBid ? b.price - a.price : a.price - b.price));

    // Recalculate cumulative totals
    let cumulative = 0;
    return sorted.map((level) => {
        cumulative += level.size;
        return { ...level, total: cumulative };
    });
}

/**
 * Hook for subscribing to real-time orderbook updates.
 */
export function useOrderbook(symbol: string): OrderBookData {
    const [bids, setBids] = useState<OrderBookLevel[]>([]);
    const [asks, setAsks] = useState<OrderBookLevel[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
    const bidsRef = useRef<OrderBookLevel[]>([]);
    const asksRef = useRef<OrderBookLevel[]>([]);

    // Keep refs in sync for delta updates
    useEffect(() => {
        bidsRef.current = bids;
    }, [bids]);

    useEffect(() => {
        asksRef.current = asks;
    }, [asks]);

    const handleMessage = useCallback((msg: unknown) => {
        const message = msg as RawOrderBookMessage;

        if (message.type === "snapshot") {
            // Full orderbook snapshot
            const newBids = processLevels(message.data.bids);
            const newAsks = processLevels(message.data.asks);
            setBids(newBids);
            setAsks(newAsks);
        } else if (message.type === "delta") {
            // Incremental update
            if (message.data.bids?.length) {
                setBids((prev) => mergeDelta(prev, message.data.bids, true));
            }
            if (message.data.asks?.length) {
                setAsks((prev) => mergeDelta(prev, message.data.asks, false));
            }
        }

        setLastUpdate(new Date());
    }, []);

    useEffect(() => {
        // Connect to WebSocket
        wsClient.connect();

        // Subscribe to orderbook channel
        const channel = `orderbook.${symbol}`;
        const subscription = wsClient.subscribe(channel, handleMessage);

        // Connection handlers
        const handleConnect = () => setIsConnected(true);
        const handleDisconnect = () => setIsConnected(false);

        wsClient.on("connect", handleConnect);
        wsClient.on("disconnect", handleDisconnect);

        // Set initial connection state
        setIsConnected(wsClient.connected);

        return () => {
            subscription.unsubscribe();
            wsClient.off("connect", handleConnect);
            wsClient.off("disconnect", handleDisconnect);
        };
    }, [symbol, handleMessage]);

    // Calculate spread
    const spread = asks[0]?.price && bids[0]?.price ? asks[0].price - bids[0].price : 0;

    return { bids, asks, spread, isConnected, lastUpdate };
}
