"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    TrendingUp,
    Wallet,
    History,
    Settings,
    ChevronLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/lib/stores/ui-store";

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
    const { sidebarOpen, toggleSidebar } = useUIStore();

    return (
        <aside
            className={cn(
                "fixed left-0 top-0 z-40 h-screen border-r border-border bg-card transition-all duration-300",
                sidebarOpen ? "w-56" : "w-16"
            )}
        >
            {/* Logo */}
            <div className="flex h-14 items-center justify-between border-b border-border px-4">
                {sidebarOpen && (
                    <span className="text-lg font-bold text-foreground">
                        AgenticTrader
                    </span>
                )}
                <button
                    onClick={toggleSidebar}
                    className="rounded-md p-1.5 hover:bg-accent"
                >
                    <ChevronLeft
                        className={cn(
                            "h-5 w-5 text-muted-foreground transition-transform",
                            !sidebarOpen && "rotate-180"
                        )}
                    />
                </button>
            </div>

            {/* Navigation */}
            <nav className="flex flex-col gap-1 p-2">
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                                isActive
                                    ? "bg-primary text-primary-foreground"
                                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                            )}
                        >
                            <item.icon className="h-5 w-5 shrink-0" />
                            {sidebarOpen && <span>{item.label}</span>}
                        </Link>
                    );
                })}
            </nav>
        </aside>
    );
}
