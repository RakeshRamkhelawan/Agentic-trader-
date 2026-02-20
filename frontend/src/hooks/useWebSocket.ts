/**
 * WebSocket Hook v2 - Reliable WebSocket Connection Management
 * 
 * Implements ADR-003: WebSocket Reliability & Backpressure
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Heartbeat/ping-pong handling
 * - Resync signaling
 * - Connection state management
 * - Idempotent subscriptions
 * 
 * @author Architecture Team
 * @date 2026-02-20
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';

export interface WSMessage {
  type: string;
  stream?: string;
  ts?: string;
  seq?: number;
  priority?: 'high' | 'low';
  data?: unknown;
  [key: string]: unknown;
}

export interface WSConfig {
  /** WebSocket URL (ws:// or wss://) */
  url: string;
  /** Auth token for connection */
  token: string;
  /** Initial streams to subscribe to */
  streams?: string[];
  /** Callback for incoming messages */
  onMessage: (message: WSMessage) => void;
  /** Callback when connection established */
  onConnect?: () => void;
  /** Callback when connection lost */
  onDisconnect?: (reason: string) => void;
  /** Callback for resync signal */
  onResyncRequired?: () => void;
  /** Enable automatic reconnection (default: true) */
  reconnect?: boolean;
  /** Maximum reconnect attempts (0 = infinite, default: 10) */
  maxReconnectAttempts?: number;
  /** Base delay for exponential backoff in ms (default: 1000) */
  reconnectBaseDelay?: number;
  /** Maximum reconnect delay in ms (default: 30000) */
  reconnectMaxDelay?: number;
  /** Jitter factor 0-1 (default: 0.3) */
  jitterFactor?: number;
}

export interface WSState {
  /** Current connection status */
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  /** Number of reconnection attempts made */
  reconnectCount: number;
  /** Last error message */
  lastError?: string;
  /** Connection latency in ms (if available) */
  latency?: number;
}

/**
 * React hook for reliable WebSocket connections
 * 
 * @example
 * ```tsx
 * const { state, send, subscribe, unsubscribe, disconnect, reconnect } = useWebSocket({
 *   url: 'ws://localhost:8000/ws',
 *   token: accessToken,
 *   streams: ['ticker.BTC-EUR', 'portfolio'],
 *   onMessage: (msg) => console.log('Received:', msg),
 *   onResyncRequired: () => fetchSnapshot(),
 * });
 * ```
 */
export function useWebSocket(config: WSConfig) {
  // Configuration with defaults
  const {
    reconnect = true,
    maxReconnectAttempts = 10,
    reconnectBaseDelay = 1000,
    reconnectMaxDelay = 30000,
    jitterFactor = 0.3,
    streams = [],
  } = config;

  // State
  const [state, setState] = useState<WSState>({
    status: 'disconnected',
    reconnectCount: 0,
  });

  // Refs for mutable values that shouldn't trigger re-renders
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);
  const subscribedStreamsRef = useRef<Set<string>>(new Set(streams));
  const connectionStartTimeRef = useRef<number>(0);
  
  // Track if component is mounted
  const isMountedRef = useRef(true);

  /**
   * Calculate reconnect delay with exponential backoff and jitter
   */
  const calculateReconnectDelay = useCallback((): number => {
    const attempt = reconnectCountRef.current;
    const baseDelay = Math.min(
      reconnectBaseDelay * Math.pow(2, attempt),
      reconnectMaxDelay
    );
    const jitter = Math.random() * jitterFactor * baseDelay;
    return Math.floor(baseDelay + jitter);
  }, [reconnectBaseDelay, reconnectMaxDelay, jitterFactor]);

  /**
   * Send a message to the server
   */
  const send = useCallback((message: object): boolean => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      try {
        ws.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        return false;
      }
    }
    return false;
  }, []);

  /**
   * Subscribe to a stream/channel
   */
  const subscribe = useCallback((stream: string): boolean => {
    subscribedStreamsRef.current.add(stream);
    return send({
      type: 'subscribe',
      streams: [stream],
    });
  }, [send]);

  /**
   * Unsubscribe from a stream/channel
   */
  const unsubscribe = useCallback((stream: string): boolean => {
    subscribedStreamsRef.current.delete(stream);
    return send({
      type: 'unsubscribe',
      streams: [stream],
    });
  }, [send]);

  /**
   * Clear all timers
   */
  const clearTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  /**
   * Handle incoming messages
   */
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WSMessage = JSON.parse(event.data);

      // Handle ping from server
      if (message.type === 'ping') {
        send({
          type: 'pong',
          ts: new Date().toISOString(),
        });
        return;
      }

      // Handle resync signal
      if (message.type === 'resync_required') {
        console.warn('WebSocket resync required:', message.reason);
        config.onResyncRequired?.();
        return;
      }

      // Handle connection confirmation
      if (message.type === 'connected') {
        console.log('WebSocket connected:', message.connection_id);
        
        // Calculate connection latency
        if (connectionStartTimeRef.current) {
          const latency = Date.now() - connectionStartTimeRef.current;
          setState(prev => ({ ...prev, latency }));
        }
        
        // Resubscribe to all previously subscribed streams
        if (subscribedStreamsRef.current.size > 0) {
          send({
            type: 'subscribe',
            streams: Array.from(subscribedStreamsRef.current),
          });
        }
        
        config.onConnect?.();
        return;
      }

      // Handle subscription confirmation
      if (message.type === 'subscribed') {
        console.log('Subscribed to:', message.channel);
        return;
      }

      // Pass other messages to handler
      config.onMessage(message);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }, [config, send]);

  /**
   * Handle connection open
   */
  const handleOpen = useCallback(() => {
    if (!isMountedRef.current) return;
    
    console.log('WebSocket connection opened');
    reconnectCountRef.current = 0;
    
    setState({
      status: 'connected',
      reconnectCount: 0,
      lastError: undefined,
    });
  }, []);

  /**
   * Handle connection close
   */
  const handleClose = useCallback((event: CloseEvent) => {
    if (!isMountedRef.current) return;
    
    console.log(`WebSocket closed: ${event.code} - ${event.reason}`);
    wsRef.current = null;

    const reason = event.wasClean ? 'clean' : 'error';
    
    setState(prev => ({
      ...prev,
      status: 'disconnected',
      lastError: event.reason || 'Connection closed',
    }));

    config.onDisconnect?.(reason);

    // Schedule reconnection if enabled
    if (reconnect && isMountedRef.current) {
      if (maxReconnectAttempts === 0 || reconnectCountRef.current < maxReconnectAttempts) {
        const delay = calculateReconnectDelay();
        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectCountRef.current + 1})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectCountRef.current += 1;
          setState(prev => ({
            ...prev,
            status: 'connecting',
            reconnectCount: reconnectCountRef.current,
          }));
          connect();
        }, delay);
      } else {
        console.error('Max reconnection attempts reached');
        setState(prev => ({
          ...prev,
          status: 'error',
          lastError: 'Max reconnection attempts reached',
        }));
      }
    }
  }, [config, reconnect, maxReconnectAttempts, calculateReconnectDelay]);

  /**
   * Handle connection error
   */
  const handleError = useCallback((error: Event) => {
    console.error('WebSocket error:', error);
    setState(prev => ({
      ...prev,
      status: 'error',
      lastError: 'Connection error',
    }));
  }, []);

  /**
   * Establish WebSocket connection
   */
  const connect = useCallback(() => {
    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Build URL with auth token
    const url = new URL(config.url);
    url.searchParams.set('token', config.token);

    connectionStartTimeRef.current = Date.now();
    
    try {
      const ws = new WebSocket(url.toString());
      wsRef.current = ws;

      ws.onopen = handleOpen;
      ws.onmessage = handleMessage;
      ws.onclose = handleClose;
      ws.onerror = handleError;

      setState(prev => ({
        ...prev,
        status: 'connecting',
      }));
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setState(prev => ({
        ...prev,
        status: 'error',
        lastError: 'Failed to create connection',
      }));
    }
  }, [config.url, config.token, handleOpen, handleMessage, handleClose, handleError]);

  /**
   * Manually disconnect
   */
  const disconnect = useCallback(() => {
    clearTimers();
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    reconnectCountRef.current = 0;
    setState({
      status: 'disconnected',
      reconnectCount: 0,
    });
  }, [clearTimers]);

  /**
   * Manually reconnect
   */
  const reconnect = useCallback(() => {
    disconnect();
    reconnectCountRef.current = 0;
    setTimeout(connect, 100);
  }, [disconnect, connect]);

  // Initial connection
  useEffect(() => {
    isMountedRef.current = true;
    connect();

    return () => {
      isMountedRef.current = false;
      clearTimers();
      wsRef.current?.close(1000, 'Component unmount');
    };
  }, [connect, clearTimers]);

  // Memoized return value
  return useMemo(() => ({
    state,
    send,
    subscribe,
    unsubscribe,
    disconnect,
    reconnect,
    isConnected: state.status === 'connected',
    isConnecting: state.status === 'connecting',
  }), [state, send, subscribe, unsubscribe, disconnect, reconnect]);
}

export default useWebSocket;
