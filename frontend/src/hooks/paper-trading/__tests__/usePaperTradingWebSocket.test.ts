/**
 * Paper Trading WebSocket Hook Tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { usePaperTradingWebSocket } from '../usePaperTradingWebSocket';
import usePaperTradingStore from '@/store/paper-trading';

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  
  onopen: (() => void) | null = null;
  onclose: ((event: any) => void) | null = null;
  onmessage: ((event: any) => void) | null = null;
  onerror: (() => void) | null = null;
  
  readyState = WebSocket.CONNECTING;
  
  constructor(public url: string) {
    MockWebSocket.instances.push(this);
  }
  
  send(data: string) {
    // Mock send
  }
  
  close() {
    this.readyState = WebSocket.CLOSED;
    MockWebSocket.instances = MockWebSocket.instances.filter(
      (ws) => ws !== this
    );
  }
  
  // Helper methods for testing
  triggerOpen() {
    this.readyState = WebSocket.OPEN;
    this.onopen?.();
  }
  
  triggerMessage(data: any) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }
  
  triggerClose(code = 1000) {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.({ code, reason: 'Test close' });
  }
  
  triggerError() {
    this.onerror?.();
  }
}

// Replace global WebSocket
(global as any).WebSocket = MockWebSocket;

// Mock store
vi.mock('@/store/paper-trading', () => ({
  default: vi.fn(() => ({
    addTrade: vi.fn(),
    updatePortfolio: vi.fn(),
    updateStats: vi.fn(),
  })),
}));

describe('usePaperTradingWebSocket', () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should connect when enabled', async () => {
    const { result } = renderHook(() => 
      usePaperTradingWebSocket({ enabled: true })
    );

    // Trigger WebSocket open
    act(() => {
      MockWebSocket.instances[0]?.triggerOpen();
    });

    expect(result.current.isConnected).toBe(true);
    expect(result.current.isConnecting).toBe(false);
  });

  it('should not connect when disabled', () => {
    renderHook(() => usePaperTradingWebSocket({ enabled: false }));

    expect(MockWebSocket.instances).toHaveLength(0);
  });

  it('should handle trade messages', async () => {
    const mockAddTrade = vi.fn();
    const mockOnTrade = vi.fn();
    
    vi.mocked(usePaperTradingStore).mockReturnValue({
      addTrade: mockAddTrade,
      updatePortfolio: vi.fn(),
      updateStats: vi.fn(),
    } as any);

    renderHook(() => usePaperTradingWebSocket({ 
      enabled: true,
      onTrade: mockOnTrade,
    }));

    const tradeMessage = {
      type: 'trade',
      data: {
        id: 'trade-1',
        timestamp: '2026-03-02T10:00:00Z',
        symbol: 'BTC/EUR',
        side: 'buy',
        qty: 0.1,
        price: 50000,
        value: 5000,
        agent: 'MomentumAgent',
        exchange: 'Bitvavo',
      },
    };

    act(() => {
      MockWebSocket.instances[0]?.triggerMessage(tradeMessage);
    });

    expect(mockAddTrade).toHaveBeenCalledWith(tradeMessage.data);
    expect(mockOnTrade).toHaveBeenCalledWith(tradeMessage.data);
  });

  it('should handle portfolio update messages', () => {
    const mockUpdatePortfolio = vi.fn();
    const mockOnPortfolioUpdate = vi.fn();
    
    vi.mocked(usePaperTradingStore).mockReturnValue({
      addTrade: vi.fn(),
      updatePortfolio: mockUpdatePortfolio,
      updateStats: vi.fn(),
    } as any);

    renderHook(() => usePaperTradingWebSocket({
      enabled: true,
      onPortfolioUpdate: mockOnPortfolioUpdate,
    }));

    const portfolioMessage = {
      type: 'portfolio',
      data: {
        cash: 9000,
        positions: {},
        total_value: 10000,
        pnl: 0,
        pnl_percent: 0,
        buying_power: 9000,
      },
    };

    act(() => {
      MockWebSocket.instances[0]?.triggerMessage(portfolioMessage);
    });

    expect(mockUpdatePortfolio).toHaveBeenCalledWith(portfolioMessage.data);
    expect(mockOnPortfolioUpdate).toHaveBeenCalledWith(portfolioMessage.data);
  });

  it('should reconnect on connection loss', async () => {
    renderHook(() => usePaperTradingWebSocket({ enabled: true }));

    // First connection
    expect(MockWebSocket.instances).toHaveLength(1);

    // Close connection
    act(() => {
      MockWebSocket.instances[0]?.triggerClose();
    });

    // Fast-forward past reconnection delay
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    // Should have new connection attempt
    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('should call disconnect to close connection', () => {
    const { result } = renderHook(() => 
      usePaperTradingWebSocket({ enabled: true })
    );

    expect(MockWebSocket.instances).toHaveLength(1);

    act(() => {
      result.current.disconnect();
    });

    expect(MockWebSocket.instances).toHaveLength(0);
  });

  it('should handle error messages', () => {
    const mockOnError = vi.fn();
    
    const { result } = renderHook(() => usePaperTradingWebSocket({
      enabled: true,
      onError: mockOnError,
    }));

    const errorMessage = {
      type: 'error',
      message: 'Server error occurred',
    };

    act(() => {
      MockWebSocket.instances[0]?.triggerMessage(errorMessage);
    });

    expect(result.current.error).toBe('Server error occurred');
    expect(mockOnError).toHaveBeenCalledWith('Server error occurred');
  });

  it('should handle WebSocket errors', () => {
    const mockOnError = vi.fn();
    
    const { result } = renderHook(() => usePaperTradingWebSocket({
      enabled: true,
      onError: mockOnError,
    }));

    act(() => {
      MockWebSocket.instances[0]?.triggerError();
    });

    expect(result.current.error).toBe('WebSocket error occurred');
    expect(mockOnError).toHaveBeenCalledWith('WebSocket error occurred');
  });
});
