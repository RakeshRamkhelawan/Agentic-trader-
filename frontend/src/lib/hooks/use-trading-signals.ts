"use client";

import { useState, useEffect, useCallback } from "react";
import { wsClient, type Subscription, type IncomingMessage } from "@/lib/api/websocket-client";

/**
 * Signal types from AI agents
 */
export type SignalType = "buy" | "sell" | "hold" | "alert" | "info";

/**
 * Confidence levels for signals
 */
export type SignalConfidence = "high" | "medium" | "low";

/**
 * A trading signal from an AI agent
 */
export interface TradingSignal {
    signalId: string;
    agentId: string;
    agentName: string;
    symbol: string;
    signalType: SignalType;
    confidence: SignalConfidence;
    message: string;
    reasoning?: string;
    targetPrice?: number;
    stopLoss?: number;
    metadata?: {
        originalType?: string;
        gunaVibration?: {
            sattva: number;
            rajas: number;
            tamas: number;
        };
        sentimentScore?: number;
        marketRegime?: string;
    };
    timestamp: Date;
}

/**
 * Raw signal message from WebSocket
 */
interface RawSignalMessage {
    signal_id: string;
    agent_id: string;
    agent_name: string;
    symbol: string;
    signal_type: string;
    confidence: string;
    message: string;
    reasoning?: string;
    target_price?: number;
    stop_loss?: number;
    metadata?: Record<string, unknown>;
    timestamp: string;
}

/**
 * Options for the useTradingSignals hook
 */
interface UseTradingSignalsOptions {
    /** Filter by specific agent ID */
    agentId?: string;
    /** Filter by specific symbol */
    symbol?: string;
    /** Filter by signal types */
    signalTypes?: SignalType[];
    /** Maximum number of signals to keep in history */
    maxHistory?: number;
}

/**
 * Hook for receiving real-time trading signals from AI agents.
 * 
 * @example
 * ```tsx
 * // Get all signals
 * const { signals, latestSignal, isConnected } = useTradingSignals();
 * 
 * // Filter by agent
 * const { signals } = useTradingSignals({ agentId: "sentiment_v1" });
 * 
 * // Filter by symbol
 * const { signals } = useTradingSignals({ symbol: "BTC-EUR" });
 * ```
 */
export function useTradingSignals(options: UseTradingSignalsOptions = {}) {
    const { agentId, symbol, signalTypes, maxHistory = 50 } = options;

    const [signals, setSignals] = useState<TradingSignal[]>([]);
    const [latestSignal, setLatestSignal] = useState<TradingSignal | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [unreadCount, setUnreadCount] = useState(0);

    // Parse raw signal from WebSocket
    const parseSignal = useCallback((data: RawSignalMessage): TradingSignal => {
        return {
            signalId: data.signal_id,
            agentId: data.agent_id,
            agentName: data.agent_name,
            symbol: data.symbol,
            signalType: data.signal_type as SignalType,
            confidence: data.confidence as SignalConfidence,
            message: data.message,
            reasoning: data.reasoning,
            targetPrice: data.target_price,
            stopLoss: data.stop_loss,
            metadata: data.metadata
                ? {
                    originalType: data.metadata.original_type as string,
                    gunaVibration: data.metadata.guna_vibration as {
                        sattva: number;
                        rajas: number;
                        tamas: number;
                    },
                    sentimentScore: data.metadata.sentiment_score as number,
                    marketRegime: data.metadata.market_regime as string,
                }
                : undefined,
            timestamp: new Date(data.timestamp),
        };
    }, []);

    // Filter signal based on options
    const shouldIncludeSignal = useCallback(
        (signal: TradingSignal): boolean => {
            if (agentId && signal.agentId !== agentId) return false;
            if (symbol && signal.symbol !== symbol) return false;
            if (signalTypes && !signalTypes.includes(signal.signalType))
                return false;
            return true;
        },
        [agentId, symbol, signalTypes]
    );

    // Load last read timestamp from localStorage
    const [lastReadTimestamp, setLastReadTimestamp] = useState<Date>(() => {
        if (typeof window !== "undefined") {
            const stored = localStorage.getItem("signals_last_read");
            return stored ? new Date(stored) : new Date(0);
        }
        return new Date(0);
    });

    // Mark all signals as read
    const markAllRead = useCallback(() => {
        setUnreadCount(0);
        const now = new Date();
        setLastReadTimestamp(now);
        if (typeof window !== "undefined") {
            localStorage.setItem("signals_last_read", now.toISOString());
        }
    }, []);

    // Clear signal history
    const clearHistory = useCallback(() => {
        setSignals([]);
        setLatestSignal(null);
        setUnreadCount(0);
        // Also update read timestamp to now
        const now = new Date();
        setLastReadTimestamp(now);
        if (typeof window !== "undefined") {
            localStorage.setItem("signals_last_read", now.toISOString());
        }
    }, []);

    useEffect(() => {
        // Determine which channel to subscribe to
        const channel = agentId ? `signals.${agentId}` : "signals";

        // Subscribe to signals channel
        const subscription: Subscription = wsClient.subscribe(
            channel,
            (msg) => {
                // Cast to extended message type that includes 'signal'
                const message = msg as { channel: string; type: string; data: unknown };
                if (message.type === "snapshot") {
                    // Handle initial snapshot
                    const snapshotData: unknown = message.data;
                    if (Array.isArray(snapshotData)) {
                        const rawSignals = snapshotData as RawSignalMessage[];
                        const parsedSignals = rawSignals
                            .map(parseSignal)
                            .filter(shouldIncludeSignal);
                        setSignals(parsedSignals.slice(-maxHistory));
                        if (parsedSignals.length > 0) {
                            setLatestSignal(parsedSignals[parsedSignals.length - 1]);
                        }

                        // Calculate unread count based on stored timestamp
                        const unread = parsedSignals.filter(s => s.timestamp > lastReadTimestamp).length;
                        setUnreadCount(unread);
                    }
                } else if (message.type === "signal" || message.type === "update") {
                    // Handle new signal
                    const rawSignal = message.data as RawSignalMessage;
                    const signal = parseSignal(rawSignal);

                    if (shouldIncludeSignal(signal)) {
                        setSignals((prev) => {
                            const updated = [...prev, signal];
                            // Keep only the last maxHistory signals
                            return updated.slice(-maxHistory);
                        });
                        setLatestSignal(signal);

                        // Increment unread count only if it's newer than last read (which it should be)
                        if (signal.timestamp > lastReadTimestamp) {
                            setUnreadCount((prev) => prev + 1);
                        }
                    }
                }
            }
        );

        // Track connection status
        const checkConnection = () => {
            setIsConnected(wsClient.connected);
        };

        checkConnection();
        const connectionInterval = setInterval(checkConnection, 1000);

        // Connect if not already connected
        wsClient.connect();

        return () => {
            subscription.unsubscribe();
            clearInterval(connectionInterval);
        };
    }, [agentId, parseSignal, shouldIncludeSignal, maxHistory, lastReadTimestamp]);

    // Computed values
    const buySignals = signals.filter((s) => s.signalType === "buy");
    const sellSignals = signals.filter((s) => s.signalType === "sell");
    const alertSignals = signals.filter(
        (s) => s.signalType === "alert" || s.signalType === "info"
    );

    return {
        /** All signals matching the filter criteria */
        signals,
        /** The most recent signal */
        latestSignal,
        /** Number of buy signals */
        buySignals,
        /** Number of sell signals */
        sellSignals,
        /** Alert and info signals */
        alertSignals,
        /** Whether WebSocket is connected */
        isConnected,
        /** Number of unread signals */
        unreadCount,
        /** Mark all signals as read */
        markAllRead,
        /** Clear signal history */
        clearHistory,
    };
}
