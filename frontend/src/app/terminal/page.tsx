"use client";

import { useState } from "react";
import { usePortfolio } from "@/lib/hooks/use-portfolio";
import { TopBar } from "@/components/layout/top-bar";
import { TradingChart } from "@/components/trading/chart/trading-chart";
import { OrderBook } from "@/components/trading/orderbook/order-book";
import { OrderTicket } from "@/components/trading/order-ticket/order-ticket";
import { TradeHistory } from "@/components/trading/history/trade-history";
// import { SignalsPanel } from "@/components/trading/signals/signals-panel";
import { GlassCard } from "@/components/ui/glass-card";
// import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function TerminalPage() {
    const [symbol, setSymbol] = useState("BTC-EUR");
    const { data: portfolio } = usePortfolio();

    return (
        <div className="flex h-screen flex-col">
            <TopBar
                balance={portfolio?.total_value ?? 0}
                currency="EUR"
                selectedSymbol={symbol}
                onSymbolChange={setSymbol}
            />

            <div className="flex-1 overflow-hidden p-4">
                <div className="grid h-full gap-4 lg:grid-cols-[1fr_320px_280px]">
                    {/* Chart - Main area */}
                    {/* Chart - Main area */}
                    <GlassCard className="flex flex-col overflow-hidden">
                        <div className="border-b border-white/10 py-3 px-4 backdrop-blur-md">
                            <h3 className="text-base font-semibold text-foreground/90">Chart</h3>
                        </div>
                        <div className="flex-1 p-0">
                            <TradingChart symbol={symbol} />
                        </div>
                    </GlassCard>

                    {/* OrderBook */}
                    {/* OrderBook */}
                    <GlassCard className="flex flex-col overflow-hidden">
                        <div className="border-b border-white/10 py-3 px-4 backdrop-blur-md">
                            <h3 className="text-base font-semibold text-foreground/90">Order Book</h3>
                        </div>
                        <div className="flex-1 overflow-hidden p-0">
                            <OrderBook symbol={symbol} />
                        </div>
                    </GlassCard>

                    {/* Right column: Order Ticket + AI Signals */}
                    <div className="flex flex-col gap-4 overflow-hidden">
                        {/* Order Ticket */}
                        {/* Order Ticket */}
                        <GlassCard className="flex flex-col">
                            <div className="border-b border-white/10 py-3 px-4 backdrop-blur-md">
                                <h3 className="text-base font-semibold text-foreground/90">Place Order</h3>
                            </div>
                            <div className="p-0">
                                <OrderTicket symbol={symbol} />
                            </div>
                        </GlassCard>

                        {/* Trade History */}
                        <GlassCard className="flex flex-col flex-1 min-h-0 overflow-hidden">
                            <div className="border-b border-white/10 py-3 px-4 backdrop-blur-md">
                                <h3 className="text-base font-semibold text-foreground/90">Recent Trades</h3>
                            </div>
                            <div className="flex-1 overflow-hidden p-0">
                                <TradeHistory />
                            </div>
                        </GlassCard>

                        {/* AI Signals Panel - Hidden for now in favor of TradeHistory */}
                        {/* <SignalsPanel className="flex-1 min-h-0" maxSignals={8} /> */}
                    </div>
                </div>
            </div>
        </div>
    );
}
