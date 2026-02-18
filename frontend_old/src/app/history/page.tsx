"use client";

import { useState, useEffect } from "react";
import { TopBar } from "@/components/layout/top-bar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button, buttonVariants } from "@/components/ui/button";
import { Search, Filter, Download, ArrowUpRight, ArrowDownRight, Loader2 } from "lucide-react";
import { getHistory, Trade } from "@/lib/api/trading-api";

export default function HistoryPage() {
    const [searchQuery, setSearchQuery] = useState("");
    const [filterSide, setFilterSide] = useState<"all" | "buy" | "sell">("all");
    const [trades, setTrades] = useState<Trade[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await getHistory();
                setTrades(data);
            } catch (err) {
                setError("Failed to load trade history");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const filteredTrades = trades.filter((trade) => {
        const matchesSearch = trade.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
            trade.id.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesType = filterSide === "all" || trade.side === filterSide;
        return matchesSearch && matchesType;
    });

    const exportCSV = () => {
        const headers = ["ID", "Symbol", "Side", "Amount", "Price", "Total", "Fee", "Time", "Status"];
        const rows = filteredTrades.map(t => [
            t.id, t.symbol, t.side, t.amount, t.price, t.total, t.fee, t.time, t.status
        ]);

        const csvContent = "data:text/csv;charset=utf-8," +
            [headers.join(","), ...rows.map(e => e.join(","))].join("\n");

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "trade_history.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

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

    return (
        <div className="flex min-h-screen flex-col bg-background">
            <TopBar balance={10000} currency="EUR" />

            <div className="flex-1 p-6">
                <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Trade History</h1>
                        <p className="mt-2 text-muted-foreground">
                            View and export your past trading activity
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button variant="outline" onClick={exportCSV}>
                            <Download className="mr-2 h-4 w-4" />
                            Export CSV
                        </Button>
                    </div>
                </div>

                {/* Filters */}
                <Card className="mb-6">
                    <CardContent className="p-4">
                        <div className="flex flex-col gap-4 md:flex-row md:items-center">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                <Input
                                    placeholder="Search by symbol or order ID..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-9"
                                />
                            </div>
                            <div className="flex items-center gap-2">
                                <Filter className="h-4 w-4 text-muted-foreground" />
                                <select
                                    className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                    value={filterSide}
                                    onChange={(e) => setFilterSide(e.target.value as any)}
                                >
                                    <option value="all">All Sides</option>
                                    <option value="buy">Buy</option>
                                    <option value="sell">Sell</option>
                                </select>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Summary Cards */}
                <div className="grid gap-4 md:grid-cols-3 mb-6">
                    <Card>
                        <CardHeader className="py-4">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Total Trades</CardTitle>
                        </CardHeader>
                        <CardContent className="py-2 pb-4">
                            <div className="text-2xl font-bold">{trades.length}</div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="py-4">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Total Volume</CardTitle>
                        </CardHeader>
                        <CardContent className="py-2 pb-4">
                            <div className="text-2xl font-bold">
                                €{trades.reduce((acc, t) => acc + t.total, 0).toLocaleString("en-IE", { maximumFractionDigits: 0 })}
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="py-4">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Fees Paid</CardTitle>
                        </CardHeader>
                        <CardContent className="py-2 pb-4">
                            <div className="text-2xl font-bold text-red-500">
                                €{trades.reduce((acc, t) => acc + t.fee, 0).toLocaleString("en-IE", { maximumFractionDigits: 2 })}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Data Table */}
                <div className="rounded-md border border-border bg-card">
                    <div className="relative w-full overflow-auto">
                        <table className="w-full caption-bottom text-sm">
                            <thead className="[&_tr]:border-b">
                                <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Time</th>
                                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Pair</th>
                                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Side</th>
                                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Price</th>
                                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Amount</th>
                                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Total</th>
                                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Status</th>
                                </tr>
                            </thead>
                            <tbody className="[&_tr:last-child]:border-0">
                                {filteredTrades.length === 0 ? (
                                    <tr>
                                        <td colSpan={7} className="p-12 text-center">
                                            <div className="flex flex-col items-center justify-center gap-2">
                                                <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-2">
                                                    <Search className="h-6 w-6 text-muted-foreground opacity-50" />
                                                </div>
                                                <h3 className="font-semibold text-lg">No trades found</h3>
                                                <p className="text-sm text-muted-foreground max-w-sm mb-4">
                                                    You haven't made any trades yet, or your search query returned no results.
                                                </p>
                                                {filteredTrades.length === 0 && searchQuery === "" && (
                                                    <a href="/terminal" className={buttonVariants()}>Start Trading</a>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ) : (
                                    filteredTrades.map((trade) => (
                                        <tr key={trade.id} className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                            <td className="p-4 align-middle">{trade.time}</td>
                                            <td className="p-4 align-middle font-medium">{trade.symbol}</td>
                                            <td className="p-4 align-middle">
                                                <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${trade.side === "buy"
                                                    ? "bg-green-500/10 text-green-500"
                                                    : "bg-red-500/10 text-red-500"
                                                    }`}>
                                                    {trade.side.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="p-4 align-middle">€{trade.price.toFixed(2)}</td>
                                            <td className="p-4 align-middle">{trade.amount}</td>
                                            <td className="p-4 align-middle">€{trade.total.toFixed(2)}</td>
                                            <td className="p-4 align-middle">
                                                <div className="flex items-center gap-2">
                                                    <div className="h-2 w-2 rounded-full bg-green-500" />
                                                    <span className="capitalize">{trade.status}</span>
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
