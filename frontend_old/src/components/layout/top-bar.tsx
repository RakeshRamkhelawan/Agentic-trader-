"use client";

import { Bell, User, Wallet, ChevronDown, LogOut, Settings, History, CreditCard } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useTicker } from "@/lib/hooks/use-ticker";
import { useMarkets } from "@/lib/hooks/use-markets";
import { usePortfolio } from "@/lib/hooks/use-portfolio";
import { useState } from "react";
import Link from "next/link";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface TopBarProps {
    balance?: number;
    currency?: string;
    selectedSymbol?: string;
    onSymbolChange?: (symbol: string) => void;
}

// Removed AVAILABLE_MARKETS constant in favor of useMarkets hook

export function TopBar({
    currency = "EUR",
    selectedSymbol = "BTC-EUR",
    onSymbolChange
}: TopBarProps) {
    const { ticker, isConnected } = useTicker(selectedSymbol);
    const { data: markets } = useMarkets();
    const { data: portfolio } = usePortfolio();

    // Balance from hook (fallback to 0)
    const balance = portfolio?.total_value ?? 0;
    const [isMarketOpen, setIsMarketOpen] = useState(false);

    // Use ticker data or 0/null
    const price = ticker?.last || 0;
    const changePercent = ticker?.changePercent24h || 0;
    const isPositive = changePercent >= 0;

    const handleLogout = () => {
        if (typeof window !== "undefined") {
            localStorage.removeItem("token");
            localStorage.removeItem("refresh_token");
            window.location.href = "/login";
        }
    };

    return (
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-card/80 px-4 backdrop-blur-sm">
            {/* Market selector */}
            <div className="relative flex items-center gap-4">
                <Button
                    variant="ghost"
                    className="flex items-center gap-2 px-2 hover:bg-accent/50"
                    onClick={() => setIsMarketOpen(!isMarketOpen)}
                    data-testid="market-selector-button"
                >
                    <span className="text-lg font-semibold">{selectedSymbol.replace("-", "/")}</span>
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                </Button>

                {isMarketOpen && (
                    <div className="absolute top-12 left-0 z-50 w-56 overflow-hidden rounded-md border border-border bg-popover shadow-xl animate-in fade-in-0 zoom-in-95">
                        <div className="p-1">
                            <div className="p-1 max-h-[300px] overflow-y-auto">
                                {(markets || []).map((market) => (
                                    <button
                                        key={market.symbol}
                                        data-testid={`market-option-${market.symbol}`}
                                        className={cn(
                                            "flex w-full items-center justify-between rounded-sm px-3 py-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground",
                                            selectedSymbol === market.symbol && "bg-accent/50 font-medium"
                                        )}
                                        onClick={() => {
                                            onSymbolChange?.(market.symbol);
                                            setIsMarketOpen(false);
                                        }}
                                    >
                                        <span>{market.symbol.replace("-", "/")}</span>
                                        {/* <span className="text-xs text-muted-foreground">{market.name}</span> */}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Price Display */}
                <div className="hidden items-center gap-3 sm:flex">
                    <span className={cn(
                        "font-mono text-base font-medium",
                        isPositive ? "text-positive" : "text-negative"
                    )}>
                        {formatCurrency(price, currency)}
                    </span>
                    <span className={cn(
                        "text-sm font-medium",
                        isPositive ? "text-positive" : "text-negative"
                    )}>
                        {isPositive ? "+" : ""}{changePercent.toFixed(2)}%
                    </span>

                    {/* Connection Status Dot */}
                    <span
                        className={cn("h-2 w-2 rounded-full", isConnected ? "bg-brand-green" : "bg-brand-red")}
                        title={isConnected ? "Live" : "Disconnected"}
                    />
                </div>
            </div>

            {/* Right side: Balance + Actions */}
            {/* Right side: Balance + Actions */}
            <div className="flex items-center gap-4">
                {/* Balance - Clickable to Portfolio */}
                <Link href="/portfolio">
                    <div className="flex cursor-pointer items-center gap-2 rounded-md bg-secondary px-3 py-1.5 hover:bg-secondary/80 transition-colors">
                        <Wallet className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{formatCurrency(balance, currency)}</span>
                    </div>
                </Link>

                {/* Notifications Popover */}
                <Popover>
                    <PopoverTrigger asChild>
                        <Button variant="ghost" size="icon" className="relative">
                            <Bell className="h-5 w-5" />
                            <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-brand-red" />
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-80 p-0" align="end">
                        <div className="flex items-center justify-between border-b px-4 py-3">
                            <h4 className="font-semibold">Notifications</h4>
                            <span className="text-xs text-muted-foreground">Mark all as read</span>
                        </div>
                        <div className="max-h-[300px] overflow-y-auto">
                            <div className="p-4 text-center text-sm text-muted-foreground">
                                No new notifications
                            </div>
                        </div>
                    </PopoverContent>
                </Popover>

                {/* User Menu Dropdown */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="rounded-full">
                            <Avatar className="h-8 w-8">
                                <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="@user" />
                                <AvatarFallback>TR</AvatarFallback>
                            </Avatar>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56">
                        <DropdownMenuLabel>My Account</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem asChild>
                            <Link href="/settings">
                                <User className="mr-2 h-4 w-4" />
                                <span>Profile</span>
                            </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild>
                            <Link href="/history">
                                <History className="mr-2 h-4 w-4" />
                                <span>Trading History</span>
                            </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild>
                            <Link href="/settings?tab=preferences">
                                <Settings className="mr-2 h-4 w-4" />
                                <span>Preferences</span>
                            </Link>
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={handleLogout} className="text-red-500 focus:text-red-500">
                            <LogOut className="mr-2 h-4 w-4" />
                            <span>Log out</span>
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </header >
    );
}
