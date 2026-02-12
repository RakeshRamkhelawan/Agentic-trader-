import { create } from "zustand";
import { persist } from "zustand/middleware";

export type OrderSide = "buy" | "sell";
export type OrderType = "market" | "limit" | "stop" | "stop-limit";

interface TradingState {
    // Active market
    activeMarket: string;
    setActiveMarket: (symbol: string) => void;

    // Order form state
    orderSide: OrderSide;
    orderType: OrderType;
    quantity: string;
    limitPrice: string;
    stopPrice: string;
    setOrderSide: (side: OrderSide) => void;
    setOrderType: (type: OrderType) => void;
    setQuantity: (qty: string) => void;
    setLimitPrice: (price: string) => void;
    setStopPrice: (price: string) => void;
    resetOrderForm: () => void;

    // Leverage (for derivatives)
    leverage: number;
    setLeverage: (leverage: number) => void;
}

export const useTradingStore = create<TradingState>()(
    persist(
        (set) => ({
            // Active market
            activeMarket: "BTC-EUR",
            setActiveMarket: (symbol) => set({ activeMarket: symbol }),

            // Order form
            orderSide: "buy",
            orderType: "market",
            quantity: "",
            limitPrice: "",
            stopPrice: "",
            setOrderSide: (side) => set({ orderSide: side }),
            setOrderType: (type) => set({ orderType: type }),
            setQuantity: (qty) => set({ quantity: qty }),
            setLimitPrice: (price) => set({ limitPrice: price }),
            setStopPrice: (price) => set({ stopPrice: price }),
            resetOrderForm: () =>
                set({
                    quantity: "",
                    limitPrice: "",
                    stopPrice: "",
                }),

            // Leverage
            leverage: 1,
            setLeverage: (leverage) => set({ leverage }),
        }),
        {
            name: "trading-storage",
            partialize: (state) => ({
                activeMarket: state.activeMarket,
                leverage: state.leverage,
            }),
        }
    )
);
