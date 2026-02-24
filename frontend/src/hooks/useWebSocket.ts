/**
 * WebSocket Hook
 * 
 * Manages WebSocket connection with auto-reconnect, heartbeat, and
 * channel-based subscriptions.
 */

/* eslint-disable react-hooks/set-state-in-effect */

import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketMessage {
  type: string;
  channel?: string;
  data?: unknown;
  connection_id?: string;
  timestamp?: string;
}

interface UseWebSocketOptions {
  url: string;
  token?: string | null;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  debug?: boolean;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  lastMessage: WebSocketMessage | null;
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  sendMessage: (message: Record<string, unknown>) => void;
  connect: () => void;
  disconnect: () => void;
}

export function useWebSocket({
  url,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  token,
  onMessage,
  onConnect,
  onDisconnect,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5,
  heartbeatInterval = 30000,
  debug = false,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const subscribedChannelsRef = useRef<Set<string>>(new Set());

  const log = useCallback((...args: unknown[]) => {
    if (debug) {
      console.log('[WebSocket]', ...args);
    }
  }, [debug]);

  // Create a ref to store the connect function for use in closures
  const connectRef = useRef<(() => void) | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      log('Already connected');
      return;
    }

    setIsConnecting(true);
    log('Connecting to', url);

    try {
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        log('Connected');
        setIsConnected(true);
        setIsConnecting(false);
        reconnectAttemptsRef.current = 0;
        onConnect?.();

        // Resubscribe to channels after reconnect
        subscribedChannelsRef.current.forEach(channel => {
          wsRef.current?.send(JSON.stringify({ type: 'subscribe', channel }));
        });

        // Start heartbeat
        if (heartbeatInterval > 0) {
          heartbeatTimerRef.current = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              wsRef.current.send(JSON.stringify({ type: 'ping' }));
            }
          }, heartbeatInterval);
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          log('Received:', message);
          setLastMessage(message);
          onMessage?.(message);
        } catch {
          log('Failed to parse message:', event.data);
        }
      };

      wsRef.current.onclose = (event) => {
        log('Disconnected:', event.code, event.reason);
        setIsConnected(false);
        setIsConnecting(false);
        onDisconnect?.();

        // Clear heartbeat
        if (heartbeatTimerRef.current) {
          clearInterval(heartbeatTimerRef.current);
          heartbeatTimerRef.current = null;
        }

        // Attempt reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          log(`Reconnecting... attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`);
          // Use the ref to avoid the circular dependency
          reconnectTimerRef.current = setTimeout(() => connectRef.current?.(), reconnectInterval);
        } else {
          log('Max reconnect attempts reached');
        }
      };

      wsRef.current.onerror = (error) => {
        log('Error:', error);
        setIsConnecting(false);
      };
    } catch (_err) {
      log('Failed to create WebSocket:', _err);
      setIsConnecting(false);
    }
  }, [url, log, onConnect, onDisconnect, onMessage, reconnectInterval, maxReconnectAttempts, heartbeatInterval]);

  // Store connect in ref for use in closures
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  const disconnect = useCallback(() => {
    log('Disconnecting...');
    
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }

    // Prevent auto-reconnect on manual disconnect
    reconnectAttemptsRef.current = maxReconnectAttempts;
    
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
    setIsConnecting(false);
  }, [log, maxReconnectAttempts]);

  const subscribe = useCallback((channel: string) => {
    log('Subscribing to', channel);
    subscribedChannelsRef.current.add(channel);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'subscribe', channel }));
    }
  }, [log]);

  const unsubscribe = useCallback((channel: string) => {
    log('Unsubscribing from', channel);
    subscribedChannelsRef.current.delete(channel);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'unsubscribe', channel }));
    }
  }, [log]);

  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      log('Cannot send message, WebSocket not connected');
    }
  }, [log]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    isConnecting,
    lastMessage,
    subscribe,
    unsubscribe,
    sendMessage,
    connect,
    disconnect,
  };
}

export default useWebSocket;
