/**
 * Paper Trading WebSocket Hook
 * 
 * Provides real-time connection to paper trading WebSocket.
 * Handles automatic reconnection and message parsing.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { WS_URL } from '@/lib/config';
import {
  PAPER_TRADING_WS_PATH,
  type WebSocketMessage,
  type Trade,
  type Portfolio,
  type SessionStats,
} from '@/lib/api/paper-trading';
import usePaperTradingStore from '@/store/paper-trading';

interface UsePaperTradingWebSocketOptions {
  enabled?: boolean;
  onTrade?: (trade: Trade) => void;
  onPortfolioUpdate?: (portfolio: Portfolio) => void;
  onStatsUpdate?: (stats: SessionStats) => void;
  onError?: (error: string) => void;
}

interface UsePaperTradingWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
}

/**
 * Hook for paper trading WebSocket connection
 */
export function usePaperTradingWebSocket(
  options: UsePaperTradingWebSocketOptions = {}
): UsePaperTradingWebSocketReturn {
  const { enabled = true } = options;
  
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  
  const { addTrade, updatePortfolio, updateStats } = usePaperTradingStore();

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setIsConnecting(true);
    setError(null);

    const wsUrl = `${WS_URL}${PAPER_TRADING_WS_PATH}`;
    console.log('[PaperTrading WS] Connecting to:', wsUrl);

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[PaperTrading WS] Connected');
      setIsConnected(true);
      setIsConnecting(false);
      setError(null);
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        
        switch (message.type) {
          case 'trade':
            addTrade(message.data);
            options.onTrade?.(message.data);
            break;
            
          case 'portfolio':
            updatePortfolio(message.data);
            options.onPortfolioUpdate?.(message.data);
            break;
            
          case 'stats':
            updateStats(message.data);
            options.onStatsUpdate?.(message.data);
            break;
            
          case 'connected':
            console.log('[PaperTrading WS] Session confirmed:', message.session_id);
            break;
            
          case 'error':
            console.error('[PaperTrading WS] Server error:', message.message);
            setError(message.message);
            options.onError?.(message.message);
            break;
        }
      } catch (err) {
        console.error('[PaperTrading WS] Failed to parse message:', err);
      }
    };

    ws.onclose = (event) => {
      console.log('[PaperTrading WS] Disconnected:', event.code, event.reason);
      setIsConnected(false);
      setIsConnecting(false);
      wsRef.current = null;

      // Attempt reconnection if not manually closed
      if (enabled && reconnectAttemptsRef.current < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        console.log(`[PaperTrading WS] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current++;
          connect();
        }, delay);
      } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
        setError('Max reconnection attempts reached');
        options.onError?.('Max reconnection attempts reached');
      }
    };

    ws.onerror = (error) => {
      console.error('[PaperTrading WS] Error:', error);
      setError('WebSocket error occurred');
      setIsConnecting(false);
    };
  }, [enabled, options, addTrade, updatePortfolio, updateStats]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setIsConnecting(false);
    reconnectAttemptsRef.current = maxReconnectAttempts; // Prevent auto-reconnect
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (enabled) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    isConnected,
    isConnecting,
    error,
    connect,
    disconnect,
  };
}

export default usePaperTradingWebSocket;
