"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    TrendingUp,
    Wallet,
    History,
    Settings,
    Hexagon,
    LogIn,
    LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/auth-context";

const navItems = [
    {
        label: "Terminal",
        href: "/terminal",
        icon: LayoutDashboard,
    },
    {
        label: "Markets",
        href: "/markets",
        icon: TrendingUp,
    },
    {
        label: "Portfolio",
        href: "/portfolio",
        icon: Wallet,
    },
    {
        label: "History",
        href: "/history",
        icon: History,
    },
    {
        label: "Settings",
        href: "/settings",
        icon: Settings,
    },
];

export function Sidebar() {
    const pathname = usePathname();
    const { isAuthenticated, login, logout } = useAuth();

    return (
        <aside className="fixed left-0 top-0 z-40 flex h-screen w-16 flex-col items-center border-r border-border bg-card py-4 transition-all">
            {/* Logo */}
            <div className="mb-8 flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Hexagon className="h-6 w-6" strokeWidth={2.5} />
                <span className="sr-only">AgenticTrader Logo</span>
            </div>

            {/* Navigation */}
            <nav className="flex flex-1 flex-col gap-2">
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "group relative flex h-10 w-10 items-center justify-center rounded-xl transition-all hover:bg-accent",
                                isActive
                                    ? "bg-primary text-primary-foreground shadow-sm hover:bg-primary hover:text-primary-foreground"
                                    : "text-muted-foreground hover:text-foreground"
                            )}
                            title={item.label}
                        >
                            <item.icon className="h-5 w-5" strokeWidth={isActive ? 2.5 : 2} />
                            <span className="sr-only">{item.label}</span>

                            {/* Active Indicator Dot (Optional style choice) */}
                            {isActive && (
                                <div className="absolute -right-[1px] top-1/2 h-8 w-[3px] -translate-y-1/2 rounded-l-full bg-primary opacity-0" />
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* Bottom Actions */}
            <div className="mt-auto pb-4 flex flex-col gap-2">
                {isAuthenticated ? (
                    <button
                        onClick={() => logout()}
                        className="group relative flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground transition-all hover:bg-destructive/10 hover:text-destructive"
                        title="Logout"
                    >
                        <LogOut className="h-5 w-5" strokeWidth={2} />
                        <span className="sr-only">Logout</span>
                    </button>
                ) : (
                    <button
                        onClick={() => login()}
                        className="group relative flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground transition-all hover:bg-primary/10 hover:text-primary"
                        title="Login"
                    >
                        <LogIn className="h-5 w-5" strokeWidth={2} />
                        <span className="sr-only">Login</span>
                    </button>
                )}
            </div>
        </aside>
    );
}
