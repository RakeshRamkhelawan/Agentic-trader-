"use client";

import { useEffect, useState, useCallback } from "react";
import { wsClient, type IncomingMessage } from "@/lib/api/websocket-client";

export interface OrderUpdate {
    orderId: string;
    clientOrderId: string;
    symbol: string;
    side: "buy" | "sell";
    type: "market" | "limit" | "stop";
    status: "pending" | "open" | "filled" | "partially_filled" | "cancelled" | "rejected";
    quantity: number;
    filledQuantity: number;
    remainingQuantity: number;
    price: number;
    averagePrice: number;
    createdAt: Date;
    updatedAt: Date;
}

interface RawOrderMessage extends IncomingMessage {
    data: {
        order_id: string;
        client_order_id: string;
        symbol: string;
        side: "buy" | "sell";
        type: "market" | "limit" | "stop";
        status: string;
        quantity: number;
        filled_quantity: number;
        remaining_quantity: number;
        price: number;
        average_price: number;
        created_at: string;
        updated_at: string;
    };
}

interface UseOrdersResult {
    orders: OrderUpdate[];
    isConnected: boolean;
    lastUpdate: Date | null;
}

/**
 * Hook for subscribing to real-time order updates.
 */
export function useOrders(): UseOrdersResult {
    const [orders, setOrders] = useState<OrderUpdate[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

    const handleMessage = useCallback((msg: unknown) => {
        const message = msg as RawOrderMessage;

        if (message.type === "update") {
            const data = message.data;

            const orderUpdate: OrderUpdate = {
                orderId: data.order_id,
                clientOrderId: data.client_order_id,
                symbol: data.symbol,
                side: data.side,
                type: data.type,
                status: data.status as OrderUpdate["status"],
                quantity: data.quantity,
                filledQuantity: data.filled_quantity,
                remainingQuantity: data.remaining_quantity,
                price: data.price,
                averagePrice: data.average_price,
                createdAt: new Date(data.created_at),
                updatedAt: new Date(data.updated_at),
            };

            setOrders((prev) => {
                // Update existing order or add new one
                const existingIndex = prev.findIndex(
                    (o) => o.orderId === orderUpdate.orderId
                );
                if (existingIndex >= 0) {
                    const updated = [...prev];
                    updated[existingIndex] = orderUpdate;
                    return updated;
                }
                return [orderUpdate, ...prev];
            });

            setLastUpdate(new Date());
        } else if (message.type === "snapshot") {
            // Handle initial snapshot of all orders
            // Snapshot data comes as an array directly or wrapped in an object
            const snapshotData: unknown = message.data;
            let rawOrders: RawOrderMessage["data"][] = [];

            if (Array.isArray(snapshotData)) {
                rawOrders = snapshotData;
            } else if (snapshotData !== null && typeof snapshotData === "object" && "orders" in snapshotData) {
                const wrapped = snapshotData as { orders: unknown };
                if (Array.isArray(wrapped.orders)) {
                    rawOrders = wrapped.orders as RawOrderMessage["data"][];
                }
            }

            if (rawOrders.length > 0) {
                const mappedOrders = rawOrders.map((data) => ({
                    orderId: data.order_id,
                    clientOrderId: data.client_order_id,
                    symbol: data.symbol,
                    side: data.side,
                    type: data.type,
                    status: data.status as OrderUpdate["status"],
                    quantity: data.quantity,
                    filledQuantity: data.filled_quantity,
                    remainingQuantity: data.remaining_quantity,
                    price: data.price,
                    averagePrice: data.average_price,
                    createdAt: new Date(data.created_at),
                    updatedAt: new Date(data.updated_at),
                }));
                setOrders(mappedOrders);
            }
        }
    }, []);

    useEffect(() => {
        // Connect to WebSocket
        wsClient.connect();

        // Subscribe to orders channel
        const subscription = wsClient.subscribe("orders", handleMessage);

        // Connection handlers
        const handleConnect = () => setIsConnected(true);
        const handleDisconnect = () => setIsConnected(false);

        wsClient.on("connect", handleConnect);
        wsClient.on("disconnect", handleDisconnect);

        // Set initial connection state
        setIsConnected(wsClient.connected);

        return () => {
            subscription.unsubscribe();
            wsClient.off("connect", handleConnect);
            wsClient.off("disconnect", handleDisconnect);
        };
    }, [handleMessage]);

    return { orders, isConnected, lastUpdate };
}
