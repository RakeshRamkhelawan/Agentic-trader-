"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { wsClient, type IncomingMessage } from "@/lib/api/websocket-client";

export interface TickerData {
    symbol: string;
    bid: number;
    ask: number;
    last: number;
    volume24h: number;
    change24h: number;
    changePercent24h: number;
    high24h: number;
    low24h: number;
    timestamp: Date;
}

interface RawTickerMessage extends IncomingMessage {
    data: {
        symbol: string;
        bid: number;
        ask: number;
        last: number;
        volume_24h: number;
        change_24h: number;
        change_percent_24h: number;
        high_24h: number;
        low_24h: number;
        timestamp: string;
    };
}

interface UseTickerResult {
    ticker: TickerData | null;
    isConnected: boolean;
    previousPrice: number | null;
    priceDirection: "up" | "down" | null;
}

/**
 * Hook for subscribing to real-time ticker updates.
 */
export function useTicker(symbol: string): UseTickerResult {
    const [ticker, setTicker] = useState<TickerData | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [previousPrice, setPreviousPrice] = useState<number | null>(null);
    const [priceDirection, setPriceDirection] = useState<"up" | "down" | null>(null);

    const lastPriceRef = useRef<number | null>(null);

    const handleMessage = useCallback((msg: unknown) => {
        const message = msg as RawTickerMessage;

        if (message.type === "update" || message.type === "snapshot") {
            const data = message.data;
            const currentLast = data.last;
            const prevLast = lastPriceRef.current;

            // Track price direction
            if (prevLast !== null && currentLast !== prevLast) {
                setPreviousPrice(prevLast);
                setPriceDirection(currentLast > prevLast ? "up" : "down");

                // Reset direction after animation
                setTimeout(() => setPriceDirection(null), 500);
            }

            // Update ref
            lastPriceRef.current = currentLast;

            setTicker({
                symbol: data.symbol,
                bid: data.bid,
                ask: data.ask,
                last: data.last,
                volume24h: data.volume_24h,
                change24h: data.change_24h,
                changePercent24h: data.change_percent_24h,
                high24h: data.high_24h,
                low24h: data.low_24h,
                timestamp: new Date(data.timestamp),
            });
        }
    }, []); // No dependencies needed now

    useEffect(() => {
        // Connect to WebSocket
        wsClient.connect();

        // Subscribe to ticker channel
        const channel = `ticker.${symbol}`;
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

    return { ticker, isConnected, previousPrice, priceDirection };
}
