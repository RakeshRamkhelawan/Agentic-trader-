import { describe, it, expect, vi, beforeEach } from "vitest";
import { getMarkets, submitOrder, OrderRequest } from "./trading-api";

// Mock global fetch
global.fetch = vi.fn();

describe("tradingApi", () => {
    beforeEach(() => {
        vi.resetAllMocks();
        window.localStorage.clear();
    });

    const mockMarkets = [
        { symbol: "BTC", name: "Bitcoin", price: 50000, change: 5, volume: "10M", favorite: true }
    ];

    it("getMarkets fetches data with auth header", async () => {
        // Setup mock response
        (global.fetch as any).mockResolvedValue({
            ok: true,
            json: async () => mockMarkets
        });

        // Setup token
        window.localStorage.setItem("token", "test-token");

        const result = await getMarkets();

        // Verify fetch assertions
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining("/api/v1/trading/markets"),
            expect.objectContaining({
                headers: expect.objectContaining({
                    Authorization: "Bearer test-token"
                })
            })
        );

        // Verify result
        expect(result).toEqual(mockMarkets);
    });

    it("getMarkets handles missing token gracefully (or sends standard request)", async () => {
        // Setup mock response
        (global.fetch as any).mockResolvedValue({
            ok: true,
            json: async () => mockMarkets
        });

        // No token
        const result = await getMarkets();

        // Verify fetch assertions - Check that Authorization header is NOT present or handled
        // The implementation checks `if (token) { headers["Authorization"] = ... }`
        // so we expect NO Authorization header
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining("/api/v1/trading/markets"),
            expect.objectContaining({
                headers: expect.not.objectContaining({
                    Authorization: expect.any(String)
                })
            })
        );
    });

    it("submitOrder sends POST request with correct payload and auth", async () => {
        // Setup mock response
        (global.fetch as any).mockResolvedValue({
            ok: true,
            json: async () => ({})
        });

        window.localStorage.setItem("token", "test-token");

        const order: OrderRequest = {
            symbol: "BTC",
            side: "buy",
            type: "market",
            quantity: 1
        };

        await submitOrder(order);

        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining("/api/v1/trading/orders"),
            expect.objectContaining({
                method: "POST",
                headers: expect.objectContaining({
                    Authorization: "Bearer test-token",
                    "Content-Type": "application/json"
                }),
                body: JSON.stringify(order)
            })
        );
    });
});
