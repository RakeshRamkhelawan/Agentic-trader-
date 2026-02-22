/**
 * useWebSocket Hook
 * 
 * React hook for WebSocket connections with auto-reconnect,
 * channel subscriptions, and typed messages.
 * 
 * Usage:
 * ```tsx
 * const { isConnected, subscribe, sendMessage } = useWebSocket({
 *   url: 'wss://api.yourdomain.com/ws',
 *   token: accessToken,
 *   onConnect: () => subscribe('ticker.BTC-EUR'),
 *   onMessage: (msg) => console.log(msg)
 * });
 * ```
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketMessage {
  type: string;
  channel?: string;
  data?: unknown;
  timestamp?: string;
  connection_id?: string;
}

interface UseWebSocketOptions {
  /** WebSocket URL (ws:// or wss://) */
  url: string;
  /** JWT access token for authentication */
  token?: string | null;
  /** Called when connection is established */
  onConnect?: () => void;
  /** Called when connection is closed */
  onDisconnect?: () => void;
  /** Called when a message is received */
  onMessage?: (message: WebSocketMessage) => void;
  /** Called when an error occurs */
  onError?: (error: Event) => void;
  /** Reconnection interval in ms (default: 3000) */
  reconnectInterval?: number;
  /** Maximum reconnection attempts (default: 5) */
  maxReconnectAttempts?: number;
  /** Heartbeat interval in ms (default: 30000) */
  heartbeatInterval?: number;
  /** Enable debug logging */
  debug?: boolean;
}

interface UseWebSocketReturn {
  /** Whether the WebSocket is currently connected */
  isConnected: boolean;
  /** The last received message */
  lastMessage: WebSocketMessage | null;
  /** Send a message to the server */
  sendMessage: (message: Record<string, unknown>) => void;
  /** Subscribe to a channel */
  subscribe: (channel: string) => void;
  /** Unsubscribe from a channel */
  unsubscribe: (channel: string) => void;
  /** Manually connect */
  connect: () => void;
  /** Manually disconnect */
  disconnect: () => void;
  /** Number of reconnection attempts made */
  reconnectAttempts: number;
}

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url,
    token,
    onConnect,
    onDisconnect,
    onMessage,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000,
    debug = false
  } = options;

  const ws = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const intentionallyClosed = useRef(false);

  const log = useCallback((...args: unknown[]) => {
    if (debug) {
      console.log('[WebSocket]', ...args);
    }
  }, [debug]);

  const connect = useCallback(() => {
    // Don't reconnect if intentionally closed
    if (intentionallyClosed.current) {
      return;
    }

    // Build URL with token
    const wsUrl = token ? `${url}?token=${encodeURIComponent(token)}` : url;
    
    log('Connecting to:', wsUrl.replace(/token=[^&]+/, 'token=***'));

    try {
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        log('Connected');
        setIsConnected(true);
        setReconnectAttempts(0);
        intentionallyClosed.current = false;
        onConnect?.();

        // Start heartbeat
        if (heartbeatInterval > 0) {
          heartbeatTimer.current = setInterval(() => {
            if (ws.current?.readyState === WebSocket.OPEN) {
              ws.current.send(JSON.stringify({ type: 'ping' }));
            }
          }, heartbeatInterval);
        }
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          log('Received:', message.type, message.channel || '');
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      ws.current.onclose = (event) => {
        log('Disconnected:', event.code, event.reason);
        setIsConnected(false);
        onDisconnect?.();

        // Clear heartbeat
        if (heartbeatTimer.current) {
          clearInterval(heartbeatTimer.current);
          heartbeatTimer.current = null;
        }

        // Reconnect if not intentionally closed
        if (!intentionallyClosed.current && reconnectAttempts < maxReconnectAttempts) {
          const nextAttempt = reconnectAttempts + 1;
          log(`Reconnecting in ${reconnectInterval}ms... (${nextAttempt}/${maxReconnectAttempts})`);
          
          reconnectTimer.current = setTimeout(() => {
            setReconnectAttempts(nextAttempt);
            connect();
          }, reconnectInterval);
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          log('Max reconnection attempts reached');
        }
      };

      ws.current.onerror = (error) => {
        log('Error:', error);
        onError?.(error);
      };
    } catch (error) {
      console.error('[WebSocket] Failed to create connection:', error);
    }
  }, [url, token, reconnectInterval, maxReconnectAttempts, heartbeatInterval, reconnectAttempts, onConnect, onDisconnect, onMessage, onError, log]);

  const disconnect = useCallback(() => {
    log('Disconnecting...');
    intentionallyClosed.current = true;

    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }

    if (heartbeatTimer.current) {
      clearInterval(heartbeatTimer.current);
      heartbeatTimer.current = null;
    }

    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }

    setIsConnected(false);
    setReconnectAttempts(0);
  }, [log]);

  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
      log('Sent:', message.type || 'message');
    } else {
      console.warn('[WebSocket] Not connected, cannot send message');
    }
  }, [log]);

  const subscribe = useCallback((channel: string) => {
    sendMessage({ type: 'subscribe', channel });
  }, [sendMessage]);

  const unsubscribe = useCallback((channel: string) => {
    sendMessage({ type: 'unsubscribe', channel });
  }, [sendMessage]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, []);

  // Reconnect when token changes
  useEffect(() => {
    if (ws.current && isConnected) {
      log('Token changed, reconnecting...');
      disconnect();
      // Small delay to ensure clean disconnect
      setTimeout(connect, 100);
    }
  }, [token]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    subscribe,
    unsubscribe,
    connect,
    disconnect,
    reconnectAttempts
  };
}

export default useWebSocket;
