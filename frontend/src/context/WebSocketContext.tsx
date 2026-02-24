/**
 * WebSocket Context
 *
 * Provides a global WebSocket connection that can be used across the entire app.
 * Prevents multiple connections when multiple components use WebSocket.
 *
 * Usage:
 * ```tsx
 * // In App.tsx (wrap your app)
 * <WebSocketProvider>
 *   <App />
 * </WebSocketProvider>
 *
 * // In any component
 * const { subscribe, unsubscribe, isConnected } = useGlobalWebSocket();
 * ```
 */

/* eslint-disable react-refresh/only-export-components */

import { createContext, useContext, useCallback, useState, useEffect, type ReactNode } from 'react';
import { useWebSocket, type WebSocketMessage } from '@/hooks/useWebSocket';
import { WS_URL } from '@/lib/config';

interface WebSocketContextType {
  /** Whether the WebSocket is connected */
  isConnected: boolean;
  /** Subscribe to a channel */
  subscribe: (channel: string) => void;
  /** Unsubscribe from a channel */
  unsubscribe: (channel: string) => void;
  /** Send a message to the server */
  sendMessage: (message: Record<string, unknown>) => void;
  /** Last received message */
  lastMessage: WebSocketMessage | null;
  /** Currently subscribed channels */
  subscribedChannels: Set<string>;
  /** Connection ID from server */
  connectionId: string | null;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
  /** Additional channels to subscribe to on connect */
  defaultChannels?: string[];
}

export function WebSocketProvider({ children, defaultChannels = [] }: WebSocketProviderProps) {
  const [subscribedChannels, setSubscribedChannels] = useState<Set<string>>(new Set());
  const [connectionId, setConnectionId] = useState<string | null>(null);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    // Store connection ID when received
    if (message.type === 'connected' && message.connection_id) {
      setConnectionId(message.connection_id);
    }
  }, []);

  // Use public WebSocket endpoint for development (no auth required)
  // In production, use the authenticated endpoint with token
  const wsUrl = WS_URL;
  
  const ws = useWebSocket({
    url: wsUrl,
    token: null, // Public endpoint doesn't require token
    onMessage: handleMessage,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    heartbeatInterval: 30000,
    debug: import.meta.env.DEV,
  });

  // Subscribe to default channels on mount
  useEffect(() => {
    if (ws.isConnected && defaultChannels.length > 0) {
      defaultChannels.forEach(channel => {
        if (!subscribedChannels.has(channel)) {
          ws.subscribe(channel);
          setSubscribedChannels(prev => new Set(prev).add(channel));
        }
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ws.isConnected, defaultChannels, ws.subscribe, subscribedChannels]);

  const subscribe = useCallback((channel: string) => {
    if (!subscribedChannels.has(channel)) {
      ws.subscribe(channel);
      setSubscribedChannels(prev => new Set(prev).add(channel));
    }
  }, [ws, subscribedChannels]);

  const unsubscribe = useCallback((channel: string) => {
    if (subscribedChannels.has(channel)) {
      ws.unsubscribe(channel);
      setSubscribedChannels(prev => {
        const next = new Set(prev);
        next.delete(channel);
        return next;
      });
    }
  }, [ws, subscribedChannels]);

  const value: WebSocketContextType = {
    isConnected: ws.isConnected,
    subscribe,
    unsubscribe,
    sendMessage: ws.sendMessage,
    lastMessage: ws.lastMessage,
    subscribedChannels,
    connectionId,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

/**
 * Hook to access the global WebSocket connection.
 * Must be used within a WebSocketProvider.
 */
export function useGlobalWebSocket(): WebSocketContextType {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useGlobalWebSocket must be used within a WebSocketProvider');
  }
  return context;
}

/**
 * Hook to subscribe to a specific channel.
 * Automatically subscribes on mount and unsubscribes on unmount.
 */
export function useChannel(channel: string, onMessage?: (message: WebSocketMessage) => void) {
  const { subscribe, unsubscribe, lastMessage, isConnected } = useGlobalWebSocket();

  useEffect(() => {
    if (isConnected) {
      subscribe(channel);
      return () => unsubscribe(channel);
    }
  }, [channel, isConnected, subscribe, unsubscribe]);

  useEffect(() => {
    if (lastMessage?.channel === channel && onMessage) {
      onMessage(lastMessage);
    }
  }, [lastMessage, channel, onMessage]);

  return {
    isConnected,
    lastMessage: lastMessage?.channel === channel ? lastMessage : null,
  };
}

export default WebSocketContext;
