"use client";

import { useState, useEffect } from "react";
import { TopBar } from "@/components/layout/top-bar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight, Wallet, PieChart, Activity, Loader2 } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { getPortfolio, PortfolioStats } from "@/lib/api/trading-api";

export default function PortfolioPage() {
    const [data, setData] = useState<PortfolioStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const result = await getPortfolio();
                setData(result);
            } catch (err) {
                setError("Failed to load portfolio");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="flex min-h-screen flex-col bg-background">
                <TopBar balance={0} currency="EUR" />
                <div className="flex-1 flex justify-center items-center">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="flex min-h-screen flex-col bg-background">
                <TopBar balance={0} currency="EUR" />
                <div className="flex-1 flex justify-center items-center text-red-500">
                    {error || "No data available"}
                </div>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen flex-col bg-background">
            <TopBar balance={data.total_value} currency="EUR" />

            <div className="flex-1 p-6">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold">Portfolio</h1>
                    <p className="mt-2 text-muted-foreground">
                        Track your asset performance and allocation
                    </p>
                </div>

                {/* Summary Cards */}
                <div className="grid gap-4 md:grid-cols-3 mb-8">
                    <Card className="bg-gradient-to-br from-primary/20 to-primary/5 border-border">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total Balance</CardTitle>
                            <Wallet className="h-4 w-4 text-primary" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">€{data.total_value.toLocaleString("en-IE", { minimumFractionDigits: 2 })}</div>
                            <p className="text-xs text-muted-foreground mt-1">
                                Across all exchanges
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">24h Change</CardTitle>
                            <Activity className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className={`text-2xl font-bold flex items-center gap-2 ${data.daily_change >= 0 ? "text-green-500" : "text-red-500"}`}>
                                {data.daily_change >= 0 ? "+" : ""}€{Math.abs(data.daily_change).toLocaleString("en-IE", { minimumFractionDigits: 2 })}
                                <span className="text-sm font-normal bg-card/20 px-2 py-0.5 rounded-full border border-current/20">
                                    {data.daily_change_pct}%
                                </span>
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                                Since yesterday
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Asset Allocation</CardTitle>
                            <PieChart className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{data.holdings.length} Assets</div>
                            <div className="flex gap-1 mt-2 h-1.5 w-full rounded-full overflow-hidden">
                                {data.holdings.map((h, i) => (
                                    <div
                                        key={h.symbol}
                                        style={{ width: `${h.allocation}%` }}
                                        className={`h-full ${i % 2 === 0 ? "bg-primary" : "bg-primary/50"}`}
                                    />
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                    {/* Holdings Table */}
                    <Card className="col-span-1 border-border bg-card">
                        <CardHeader>
                            <CardTitle>Your Assets</CardTitle>
                            <CardDescription>Current holdings distribution</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-6">
                                {data.holdings.length === 0 ? (
                                    <div className="py-12 text-center flex flex-col items-center justify-center">
                                        <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-3">
                                            <Wallet className="h-6 w-6 text-muted-foreground opacity-50" />
                                        </div>
                                        <h3 className="font-semibold">Your portfolio is empty</h3>
                                        <p className="text-sm text-muted-foreground mt-1 mb-4 max-w-xs">
                                            Start trading to build your portfolio.
                                        </p>
                                        <a href="/terminal" className={buttonVariants({ variant: "outline", size: "sm" })}>
                                            Go to Terminal
                                        </a>
                                    </div>
                                ) : (
                                    data.holdings.map((holding) => (
                                        <div key={holding.symbol} className="flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
                                                    {holding.symbol.substring(0, 1)}
                                                </div>
                                                <div>
                                                    <p className="font-medium leading-none">{holding.name}</p>
                                                    <p className="text-sm text-muted-foreground">{holding.amount} {holding.symbol}</p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="font-medium">€{holding.value.toLocaleString("en-IE", { minimumFractionDigits: 2 })}</p>
                                                <p className={`text-xs ${holding.change >= 0 ? "text-green-500" : "text-red-500"}`}>
                                                    {holding.change >= 0 ? "+" : ""}{holding.change}%
                                                </p>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Recent Activity */}
                    <Card className="col-span-1 border-border bg-card">
                        <CardHeader>
                            <CardTitle>Recent Activity</CardTitle>
                            <CardDescription>Latest transactions and orders</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-6">
                                {data.recent_orders.map((order) => (
                                    <div key={order.id} className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className={`h-9 w-9 rounded-full flex items-center justify-center ${order.side === "buy" ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"
                                                }`}>
                                                {order.side === "buy" ? <ArrowDownRight className="h-5 w-5" /> : <ArrowUpRight className="h-5 w-5" />}
                                            </div>
                                            <div>
                                                <p className="font-medium leading-none">
                                                    {order.side === "buy" ? "Bought" : "Sold"} {order.symbol}
                                                </p>
                                                <p className="text-sm text-muted-foreground">{order.time}</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-medium">{order.amount} @ {order.price}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
