/**
 * Trading API Client - TypeScript client for market data and portfolio.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

// ============================================================================
// Types
// ============================================================================

export interface Market {
    symbol: string;
    name: string;
    price: number;
    change: number;
    volume: string;
    favorite: boolean;
}

export interface Holding {
    symbol: string;
    name: string;
    amount: number;
    value: number;
    change: number;
    allocation: number;
}

export interface RecentOrder {
    id: string;
    symbol: string;
    side: "buy" | "sell";
    amount: number;
    price: number;
    time: string;
}

export interface PortfolioStats {
    total_value: number;
    daily_change: number;
    daily_change_pct: number;
    holdings: Holding[];
    recent_orders: RecentOrder[];
}

export interface Trade {
    id: string;
    symbol: string;
    side: "buy" | "sell";
    amount: number;
    price: number;
    total: number;
    fee: number;
    time: string;
    status: "filled" | "canceled" | "pending";
}

// ============================================================================
// API Functions
// ============================================================================

async function apiRequest<T>(endpoint: string): Promise<T> {
    const url = `${API_BASE}${endpoint}`;

    // Add auth headers
    let token = null;
    if (typeof window !== 'undefined') {
        const resolver = (window as any)._resolveToken;
        if (resolver) {
            token = await resolver();
        }
    }

    const headers: HeadersInit = {
        "Content-Type": "application/json",
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(url, { headers });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
}

export async function getMarkets(): Promise<Market[]> {
    return apiRequest<Market[]>("/api/v1/trading/markets");
}

export async function getPortfolio(): Promise<PortfolioStats> {
    return apiRequest<PortfolioStats>("/api/v1/trading/portfolio");
}

export async function getHistory(): Promise<Trade[]> {
    return apiRequest<Trade[]>("/api/v1/trading/history");
}

export interface Candle {
    time: number;
    open: number;
    high: number;
    low: number;
    close: number;
    value: number;
}

export async function getCandles(symbol: string): Promise<Candle[]> {
    return apiRequest<Candle[]>(`/api/v1/trading/candles/${symbol}?limit=100`);
}

export interface OrderRequest {
    symbol: string;
    side: "buy" | "sell";
    type: "market" | "limit" | "stop" | "stop-limit";
    quantity: number;
    price?: number;
}

export async function submitOrder(order: OrderRequest): Promise<void> {
    const url = `/api/v1/trading/orders`;

    // In production: Add auth headers here
    let token = null;
    if (typeof window !== 'undefined') {
        const resolver = (window as any)._resolveToken;
        if (resolver) {
            token = await resolver();
        }
    }

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(order),
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
}
