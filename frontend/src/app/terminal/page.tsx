"use client";

import { TopBar } from "@/components/layout/top-bar";
import { TradingChart } from "@/components/trading/chart/trading-chart";
import { OrderBook } from "@/components/trading/orderbook/order-book";
import { OrderTicket } from "@/components/trading/order-ticket/order-ticket";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function TerminalPage() {
    const symbol = "BTC-EUR";

    return (
        <div className="flex h-screen flex-col">
            <TopBar balance={10000} currency="EUR" />

            <div className="flex-1 overflow-hidden p-4">
                <div className="grid h-full gap-4 lg:grid-cols-[1fr_320px_280px]">
                    {/* Chart - Main area */}
                    <Card className="flex flex-col overflow-hidden">
                        <CardHeader className="border-b border-border py-3">
                            <CardTitle className="text-base">Chart</CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 p-0">
                            <TradingChart symbol={symbol} />
                        </CardContent>
                    </Card>

                    {/* OrderBook */}
                    <Card className="flex flex-col overflow-hidden">
                        <CardHeader className="border-b border-border py-3">
                            <CardTitle className="text-base">Order Book</CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 overflow-hidden p-0">
                            <OrderBook symbol={symbol} />
                        </CardContent>
                    </Card>

                    {/* Order Ticket */}
                    <Card className="flex flex-col overflow-hidden">
                        <CardHeader className="border-b border-border py-3">
                            <CardTitle className="text-base">Place Order</CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <OrderTicket symbol={symbol} currentPrice={45230.5} />
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
