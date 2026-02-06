"use client";

import { Bell, User, Wallet } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface TopBarProps {
    balance?: number;
    currency?: string;
}

export function TopBar({ balance = 10000, currency = "EUR" }: TopBarProps) {
    return (
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-card/80 px-4 backdrop-blur-sm">
            {/* Market selector placeholder */}
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                    <span className="text-lg font-semibold">BTC/EUR</span>
                    <span className="text-lg font-medium text-positive">45,230.50</span>
                    <span className="text-sm text-positive">+2.34%</span>
                </div>
            </div>

            {/* Right side: Balance + Actions */}
            <div className="flex items-center gap-4">
                {/* Balance */}
                <div className="flex items-center gap-2 rounded-md bg-secondary px-3 py-1.5">
                    <Wallet className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{formatCurrency(balance, currency)}</span>
                </div>

                {/* Notifications */}
                <Button variant="ghost" size="icon" className="relative">
                    <Bell className="h-5 w-5" />
                    <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-brand-red text-2xs text-white">
                        3
                    </span>
                </Button>

                {/* User menu */}
                <Button variant="ghost" size="icon">
                    <User className="h-5 w-5" />
                </Button>
            </div>
        </header>
    );
}
