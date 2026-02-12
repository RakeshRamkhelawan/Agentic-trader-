"use client";

import { useTradingSignals, type TradingSignal } from "@/lib/hooks";
import { cn } from "@/lib/utils";

interface SignalsPanelProps {
    className?: string;
    maxSignals?: number;
}

/**
 * Get icon for signal type
 */
function getSignalIcon(type: TradingSignal["signalType"]): string {
    switch (type) {
        case "buy":
            return "arrow_upward";
        case "sell":
            return "arrow_downward";
        case "hold":
            return "pause_circle";
        case "alert":
            return "warning";
        case "info":
            return "info";
        default:
            return "notifications";
    }
}

/**
 * Get color classes for signal type
 */
function getSignalColors(type: TradingSignal["signalType"]): string {
    switch (type) {
        case "buy":
            return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
        case "sell":
            return "bg-rose-500/20 text-rose-400 border-rose-500/30";
        case "hold":
            return "bg-amber-500/20 text-amber-400 border-amber-500/30";
        case "alert":
            return "bg-orange-500/20 text-orange-400 border-orange-500/30";
        case "info":
            return "bg-blue-500/20 text-blue-400 border-blue-500/30";
        default:
            return "bg-zinc-500/20 text-zinc-400 border-zinc-500/30";
    }
}

/**
 * Format timestamp for display
 */
function formatTime(date: Date): string {
    return date.toLocaleTimeString("nl-NL", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
}

/**
 * Single signal card
 */
function SignalCard({ signal }: { signal: TradingSignal }) {
    const colors = getSignalColors(signal.signalType);

    return (
        <div
            className={cn(
                "p-3 rounded-lg border transition-all duration-200 hover:scale-[1.02]",
                colors
            )}
        >
            <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                    <span className="text-lg">
                        {signal.signalType === "buy" && "&#x2191;"}
                        {signal.signalType === "sell" && "&#x2193;"}
                        {signal.signalType === "hold" && "&#x23F8;"}
                        {signal.signalType === "alert" && "&#x26A0;"}
                        {signal.signalType === "info" && "&#x2139;"}
                    </span>
                    <div>
                        <div className="font-semibold text-sm">
                            {signal.symbol}
                        </div>
                        <div className="text-xs opacity-70">
                            {signal.agentName}
                        </div>
                    </div>
                </div>
                <div className="text-right">
                    <div
                        className={cn(
                            "text-xs px-2 py-0.5 rounded-full",
                            signal.confidence === "high" && "bg-emerald-500/30",
                            signal.confidence === "medium" && "bg-amber-500/30",
                            signal.confidence === "low" && "bg-zinc-500/30"
                        )}
                    >
                        {signal.confidence}
                    </div>
                    <div className="text-xs opacity-50 mt-1">
                        {formatTime(signal.timestamp)}
                    </div>
                </div>
            </div>
            <div className="mt-2 text-sm">{signal.message}</div>
            {signal.reasoning && (
                <div className="mt-1 text-xs opacity-60 italic">
                    {signal.reasoning}
                </div>
            )}
            {(signal.targetPrice || signal.stopLoss) && (
                <div className="mt-2 flex gap-4 text-xs">
                    {signal.targetPrice && (
                        <span>
                            Target:{" "}
                            <span className="font-mono">
                                ${signal.targetPrice.toLocaleString()}
                            </span>
                        </span>
                    )}
                    {signal.stopLoss && (
                        <span>
                            Stop:{" "}
                            <span className="font-mono">
                                ${signal.stopLoss.toLocaleString()}
                            </span>
                        </span>
                    )}
                </div>
            )}
        </div>
    );
}

/**
 * Panel displaying real-time trading signals from AI agents.
 */
export function SignalsPanel({ className, maxSignals = 10 }: SignalsPanelProps) {
    const {
        signals,
        isConnected,
        unreadCount,
        markAllRead,
        clearHistory,
        buySignals,
        sellSignals,
    } = useTradingSignals({ maxHistory: maxSignals });

    const recentSignals = signals.slice(-maxSignals).reverse();

    return (
        <div
            className={cn(
                "bg-zinc-900/50 border border-zinc-800 rounded-xl p-4",
                className
            )}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-lg">AI Signals</h3>
                    {unreadCount > 0 && (
                        <span className="bg-blue-500 text-white text-xs px-2 py-0.5 rounded-full">
                            {unreadCount} new
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {/* Connection indicator */}
                    <div
                        className={cn(
                            "w-2 h-2 rounded-full",
                            isConnected ? "bg-emerald-500" : "bg-rose-500"
                        )}
                        title={isConnected ? "Connected" : "Disconnected"}
                    />
                    {/* Actions */}
                    {unreadCount > 0 && (
                        <button
                            onClick={markAllRead}
                            className="text-xs text-zinc-400 hover:text-white transition-colors"
                        >
                            Mark read
                        </button>
                    )}
                    {signals.length > 0 && (
                        <button
                            onClick={clearHistory}
                            className="text-xs text-zinc-400 hover:text-white transition-colors"
                        >
                            Clear
                        </button>
                    )}
                </div>
            </div>

            {/* Stats bar */}
            <div className="flex gap-4 mb-4 text-sm">
                <div className="flex items-center gap-1">
                    <span className="text-emerald-400">&#x2191;</span>
                    <span>{buySignals.length} buys</span>
                </div>
                <div className="flex items-center gap-1">
                    <span className="text-rose-400">&#x2193;</span>
                    <span>{sellSignals.length} sells</span>
                </div>
                <div className="flex items-center gap-1">
                    <span className="text-zinc-400">&#x2211;</span>
                    <span>{signals.length} total</span>
                </div>
            </div>

            {/* Signal list */}
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {recentSignals.length === 0 ? (
                    <div className="text-center text-zinc-500 py-8">
                        <div className="text-2xl mb-2">&#x1F50D;</div>
                        <div>No signals yet</div>
                        <div className="text-xs mt-1">
                            AI agents are analyzing the market...
                        </div>
                    </div>
                ) : (
                    recentSignals.map((signal) => (
                        <SignalCard key={signal.signalId} signal={signal} />
                    ))
                )}
            </div>
        </div>
    );
}
