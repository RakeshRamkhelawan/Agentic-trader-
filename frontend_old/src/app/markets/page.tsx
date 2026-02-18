"use client";

import { useState, useEffect } from "react";
import { TopBar } from "@/components/layout/top-bar";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Search, Star, TrendingUp, TrendingDown, Loader2, Minus } from "lucide-react";
import { getMarkets, Market } from "@/lib/api/trading-api";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export default function MarketsPage() {
    const [searchQuery, setSearchQuery] = useState("");
    const [markets, setMarkets] = useState<Market[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await getMarkets();
                setMarkets(data);
            } catch (err) {
                setError("Failed to load markets");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const toggleFavorite = (symbol: string) => {
        setMarkets(markets.map(m =>
            m.symbol === symbol ? { ...m, favorite: !m.favorite } : m
        ));
    };

    const filteredMarkets = markets.filter(market =>
        market.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        market.symbol.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="flex min-h-screen flex-col bg-background">
            <TopBar balance={10000} currency="EUR" />

            <div className="flex-1 p-6">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold">Markets</h1>
                        <p className="mt-2 text-muted-foreground">
                            Real-time overview of cryptocurrency markets
                        </p>
                    </div>
                    <div className="relative w-72">
                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                        <Input
                            placeholder="Search markets..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 bg-card border-border"
                        />
                    </div>
                </div>

                {loading ? (
                    <div className="flex justify-center py-20">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                ) : error ? (
                    <div className="text-red-500 text-center py-10">{error}</div>
                ) : (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                        {filteredMarkets.map((market) => (
                            <Card key={market.symbol} className="overflow-hidden border-border bg-card hover:bg-card/80 transition-colors cursor-pointer group">
                                <CardContent className="p-5">
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center gap-3">
                                            <Avatar className="h-10 w-10">
                                                <AvatarImage src={`https://assets.coincap.io/assets/icons/${market.symbol.toLowerCase()}@2x.png`} alt={market.name} />
                                                <AvatarFallback className="bg-primary/10 text-primary font-bold">
                                                    {market.symbol.substring(0, 1)}
                                                </AvatarFallback>
                                            </Avatar>
                                            <div>
                                                <h3 className="font-semibold">{market.name}</h3>
                                                <p className="text-sm text-muted-foreground">{market.symbol}</p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                toggleFavorite(market.symbol);
                                            }}
                                            className={`text-muted-foreground hover:text-yellow-500 transition-colors ${market.favorite ? "text-yellow-500 fill-yellow-500" : ""}`}
                                        >
                                            <Star className={`h-5 w-5 ${market.favorite ? "fill-current" : ""}`} />
                                        </button>
                                    </div>

                                    <div className="mt-6 flex items-baseline justify-between">
                                        <div className="text-2xl font-bold">
                                            €{market.price.toLocaleString("en-IE", { minimumFractionDigits: 2, maximumFractionDigits: 6 })}
                                        </div>
                                        <div className={`flex items-center gap-1 text-sm font-medium ${market.change > 0 ? "text-green-500" :
                                            market.change < 0 ? "text-red-500" : "text-muted-foreground"
                                            }`}>
                                            {market.change > 0 ? <TrendingUp className="h-4 w-4" /> :
                                                market.change < 0 ? <TrendingDown className="h-4 w-4" /> :
                                                    <Minus className="h-4 w-4" />}
                                            {Math.abs(market.change).toFixed(2)}%
                                        </div>
                                    </div>

                                    <div className="mt-4 pt-4 border-t border-border flex justify-between text-xs text-muted-foreground">
                                        <span>Vol: {market.volume}</span>
                                        <span>24h High: €{(market.price * 1.05).toFixed(2)}</span>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
