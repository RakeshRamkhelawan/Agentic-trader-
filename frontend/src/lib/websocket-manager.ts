
type MessageHandler = (data: any) => void;

class WebSocketManager {
    private ws: WebSocket | null = null;
    private url: string;
    private handlers: Map<string, Set<MessageHandler>> = new Map();
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectInterval = 3000;

    constructor(url: string) {
        this.url = url;
    }

    connect() {
        try {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                console.log(`Connected to WebSocket: ${this.url}`);
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                const type = message.type || 'default';
                const typeHandlers = this.handlers.get(type);
                if (typeHandlers) {
                    typeHandlers.forEach(handler => handler(message.data));
                }
            };

            this.ws.onclose = () => {
                console.log(`Disconnected from WebSocket: ${this.url}`);
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error(`WebSocket Error (${this.url}):`, error);
            };
        } catch (error) {
            console.error('Failed to establish WebSocket connection:', error);
            this.attemptReconnect();
        }
    }

    private attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);
            setTimeout(() => this.connect(), this.reconnectInterval);
        }
    }

    subscribe(type: string, handler: MessageHandler) {
        if (!this.handlers.has(type)) {
            this.handlers.set(type, new Set());
        }
        this.handlers.get(type)!.add(handler);
    }

    unsubscribe(type: string, handler: MessageHandler) {
        const typeHandlers = this.handlers.get(type);
        if (typeHandlers) {
            typeHandlers.delete(handler);
        }
    }

    send(data: any) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected. Cannot send data.');
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.onclose = null; // Prevent reconnect on intentional disconnect
            this.ws.close();
            this.ws = null;
        }
    }
}

export const marketWs = new WebSocketManager(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws/market');
export const ordersWs = new WebSocketManager(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws/orders');
