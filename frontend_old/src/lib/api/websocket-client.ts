/**
 * WebSocket client for real-time trading data.
 * Handles connection management, reconnection, and message routing.
 */

type MessageHandler = (data: unknown) => void;
type ConnectionHandler = () => void;

interface Subscription {
    channel: string;
    handler: MessageHandler;
    unsubscribe: () => void;
}

interface WebSocketMessage {
    type: "subscribe" | "unsubscribe" | "ping";
    channel?: string;
    data?: unknown;
}

interface IncomingMessage {
    channel: string;
    type: "snapshot" | "delta" | "update";
    data: unknown;
}

class WebSocketClient {
    private ws: WebSocket | null = null;
    private url: string;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 10;
    private reconnectDelay = 1000;
    private subscriptions = new Map<string, Set<MessageHandler>>();
    private messageQueue: WebSocketMessage[] = [];
    private isConnected = false;
    private pingInterval: NodeJS.Timeout | null = null;
    private token: string | null = null;

    // Event handlers
    private onConnectHandlers: Set<ConnectionHandler> = new Set();
    private onDisconnectHandlers: Set<ConnectionHandler> = new Set();
    private onErrorHandlers: Set<(error: Event) => void> = new Set();

    constructor(url: string = "") {
        this.url = url || this.getDefaultUrl();
    }

    private getDefaultUrl(): string {
        if (typeof window === "undefined") return "";

        // Use the API URL from environment variables, fallback to 127.0.0.1:8000 for local dev stability
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

        // Convert http/https to ws/wss
        const wsProtocol = apiUrl.startsWith("https") ? "wss" : "ws";
        const host = apiUrl.replace(/^https?:\/\//, "").replace(/\/$/, "");

        const url = `${wsProtocol}://${host}/ws`;
        console.log("[WS] Default URL calculated:", url);
        return url;
    }

    /**
     * Connect to the WebSocket server.
     */
    connect(): void {
        if (this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING) {
            return;
        }

        try {
            let finalUrl = this.url;
            if (this.token) {
                const separator = finalUrl.includes("?") ? "&" : "?";
                finalUrl += `${separator}token=${encodeURIComponent(this.token)}`;
            }

            console.log("[WS] Connecting to", finalUrl.split("token=")[0] + (this.token ? "token=***" : ""));
            this.ws = new WebSocket(finalUrl);

            this.ws.onopen = () => {
                console.log("[WS] Connected to", this.url);
                this.isConnected = true;
                this.reconnectAttempts = 0;

                // Notify handlers
                this.onConnectHandlers.forEach((handler) => handler());

                // Process queued messages
                this.flushQueue();

                // Resubscribe to all channels
                this.resubscribeAll();

                // Start ping interval
                this.startPing();
            };

            this.ws.onclose = (event) => {
                console.log("[WS] Disconnected:", event.code, event.reason);
                this.isConnected = false;
                this.stopPing();

                // Notify handlers
                this.onDisconnectHandlers.forEach((handler) => handler());

                // Attempt reconnection
                this.scheduleReconnect();
            };

            this.ws.onerror = (error) => {
                console.error("[WS] Error object details:", {
                    readyState: this.ws?.readyState,
                    url: this.ws?.url,
                    type: error.type
                });
                console.error("[WS] Error Event:", error);
                this.onErrorHandlers.forEach((handler) => handler(error));
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(event.data);
            };
        } catch (error) {
            console.error("[WS] Connection failed:", error);
            this.scheduleReconnect();
        }
    }

    /**
     * Disconnect from the WebSocket server.
     */
    disconnect(): void {
        this.stopPing();
        if (this.ws) {
            this.ws.close(1000, "Client disconnect");
            this.ws = null;
        }
        this.isConnected = false;
    }

    /**
     * Subscribe to a channel.
     */
    subscribe(channel: string, handler: MessageHandler): Subscription {
        // Add to local subscriptions
        if (!this.subscriptions.has(channel)) {
            this.subscriptions.set(channel, new Set());
        }
        this.subscriptions.get(channel)!.add(handler);

        // Send subscribe message
        this.send({ type: "subscribe", channel });

        return {
            channel,
            handler,
            unsubscribe: () => this.unsubscribe(channel, handler),
        };
    }

    /**
     * Unsubscribe from a channel.
     */
    unsubscribe(channel: string, handler: MessageHandler): void {
        const handlers = this.subscriptions.get(channel);
        if (handlers) {
            handlers.delete(handler);
            if (handlers.size === 0) {
                this.subscriptions.delete(channel);
                this.send({ type: "unsubscribe", channel });
            }
        }
    }

    /**
     * Register a connection event handler.
     */
    on(event: "connect", handler: ConnectionHandler): void;
    on(event: "disconnect", handler: ConnectionHandler): void;
    on(event: "error", handler: (error: Event) => void): void;
    on(
        event: "connect" | "disconnect" | "error",
        handler: ConnectionHandler | ((error: Event) => void)
    ): void {
        switch (event) {
            case "connect":
                this.onConnectHandlers.add(handler as ConnectionHandler);
                break;
            case "disconnect":
                this.onDisconnectHandlers.add(handler as ConnectionHandler);
                break;
            case "error":
                this.onErrorHandlers.add(handler as (error: Event) => void);
                break;
        }
    }

    /**
     * Remove an event handler.
     */
    off(event: "connect" | "disconnect" | "error", handler: unknown): void {
        switch (event) {
            case "connect":
                this.onConnectHandlers.delete(handler as ConnectionHandler);
                break;
            case "disconnect":
                this.onDisconnectHandlers.delete(handler as ConnectionHandler);
                break;
            case "error":
                this.onErrorHandlers.delete(handler as (error: Event) => void);
                break;
        }
    }

    /**
     * Check if connected.
     */
    get connected(): boolean {
        return this.isConnected;
    }

    // Private methods

    private send(message: WebSocketMessage): void {
        if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            // Queue message for later
            this.messageQueue.push(message);
        }
    }

    private flushQueue(): void {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift()!;
            this.send(message);
        }
    }

    private resubscribeAll(): void {
        for (const channel of this.subscriptions.keys()) {
            this.send({ type: "subscribe", channel });
        }
    }

    private handleMessage(data: string): void {
        try {
            const message = JSON.parse(data) as IncomingMessage;

            // Route to channel handlers
            const handlers = this.subscriptions.get(message.channel);
            if (handlers) {
                handlers.forEach((handler) => handler(message));
            }
        } catch (error) {
            console.error("[WS] Failed to parse message:", error);
        }
    }

    private scheduleReconnect(): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error("[WS] Max reconnection attempts reached");
            return;
        }

        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
        console.log(`[WS] Reconnecting in ${delay}ms...`);

        setTimeout(() => {
            this.reconnectAttempts++;
            this.connect();
        }, delay);
    }

    private startPing(): void {
        this.pingInterval = setInterval(() => {
            this.send({ type: "ping" });
        }, 30000);
    }

    private stopPing(): void {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    /**
     * Set the authentication token for the WebSocket connection.
     * If already connected, it will stay connected until the next reconnection,
     * or you can manually call disconnect() then connect().
     */
    setToken(token: string | null): void {
        this.token = token;
        console.log("[WS] Token updated");

        // If we're not connected or connecting, try to connect now
        if (token && !this.isConnected && (!this.ws || this.ws.readyState === WebSocket.CLOSED)) {
            this.connect();
        }
    }
}

// Export singleton instance
export const wsClient = new WebSocketClient();

// Export class for custom instances
export { WebSocketClient };
export type { Subscription, IncomingMessage };
