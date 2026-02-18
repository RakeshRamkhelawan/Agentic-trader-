import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { TopBar } from "./top-bar";
import { describe, it, expect, vi } from "vitest";

// Mock hooks
vi.mock("@/lib/hooks/use-ticker", () => ({
    useTicker: () => ({
        ticker: { last: 50000, changePercent24h: 2.5 },
        isConnected: true,
    }),
}));

// Mock useMarkets (we will create this hook next)
vi.mock("@/lib/hooks/use-markets", () => ({
    useMarkets: () => ({
        data: [
            { symbol: "BTC-EUR", name: "Bitcoin / Euro", price: 50000, change: 2.5 },
            { symbol: "ETH-EUR", name: "Ethereum / Euro", price: 3000, change: -1.2 },
        ],
        isLoading: false,
    }),
}));

// Mock usePortfolio (we will use this in TopBar instead of prop)
vi.mock("@/lib/hooks/use-portfolio", () => ({
    usePortfolio: () => ({
        data: { total_value: 12500.50 },
        isLoading: false,
    }),
}));

// Mock next/navigation
vi.mock("next/navigation", () => ({
    useRouter: () => ({ push: vi.fn() }),
    usePathname: () => "/terminal",
}));

describe("TopBar Component", () => {
    it("renders with market selector and balance", () => {
        render(<TopBar />);

        // Check Market Selector default
        expect(screen.getByText("BTC/EUR")).toBeInTheDocument();

        // Check Balance (formatted)
        // Check Balance (formatted Dutch locale)
        expect(screen.getByText(/€\s?12\.500,50/)).toBeInTheDocument();
    });

    it("opens market selector and shows options from useMarkets", async () => {
        render(<TopBar />);

        // Click selector
        fireEvent.click(screen.getByTestId("market-selector-button"));

        // Check options
        await waitFor(() => {
            expect(screen.getByTestId("market-option-ETH-EUR")).toBeInTheDocument();
        });
    });

    it("calls onSymbolChange when a market is selected", async () => {
        const onSymbolChange = vi.fn();
        render(<TopBar onSymbolChange={onSymbolChange} selectedSymbol="BTC-EUR" />);

        // Click selector
        fireEvent.click(screen.getByTestId("market-selector-button"));

        // Click ETH/EUR
        fireEvent.click(screen.getByTestId("market-option-ETH-EUR"));

        expect(onSymbolChange).toHaveBeenCalledWith("ETH-EUR"); // Original symbol passed back
    });
});
