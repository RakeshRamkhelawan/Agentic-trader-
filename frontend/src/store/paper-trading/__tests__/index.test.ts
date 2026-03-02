/**
 * Paper Trading Store Tests
 * 
 * Tests for paper trading state management.
 * Follows TDD methodology.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import usePaperTradingStore, {
  selectPortfolioValue,
  selectPortfolioPnl,
  selectPortfolioPnlPercent,
  selectActivePositions,
  selectTradeCount,
  selectBuyTrades,
  selectSellTrades,
} from '../index';
import * as api from '@/lib/api/paper-trading';

// Mock the API
vi.mock('@/lib/api/paper-trading', () => ({
  paperTradingApi: {
    startSession: vi.fn(),
    stopSession: vi.fn(),
    getSessionStatus: vi.fn(),
    getPortfolio: vi.fn(),
    getTradeHistory: vi.fn(),
  },
}));

describe('PaperTradingStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    const { result } = renderHook(() => usePaperTradingStore());
    act(() => {
      result.current.reset();
    });
    vi.clearAllMocks();
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => usePaperTradingStore());

      expect(result.current.sessionId).toBeNull();
      expect(result.current.isRunning).toBe(false);
      expect(result.current.portfolio).toBeNull();
      expect(result.current.trades).toEqual([]);
      expect(result.current.stats).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('startSession', () => {
    it('should start session and update state on success', async () => {
      const mockResponse = {
        status: 'started' as const,
        session_id: 'session-123',
        started_at: '2026-03-02T10:00:00Z',
      };
      vi.mocked(api.paperTradingApi.startSession).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => usePaperTradingStore());

      await act(async () => {
        await result.current.startSession({ duration: 8, capital: 10000 });
      });

      expect(result.current.sessionId).toBe('session-123');
      expect(result.current.isRunning).toBe(true);
      expect(result.current.config).toEqual({ duration: 8, capital: 10000 });
      expect(result.current.isStarting).toBe(false);
    });

    it('should set error on failure', async () => {
      vi.mocked(api.paperTradingApi.startSession).mockRejectedValue(
        new Error('Failed to start')
      );

      const { result } = renderHook(() => usePaperTradingStore());

      await act(async () => {
        try {
          await result.current.startSession({ duration: 8, capital: 10000 });
        } catch {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe('Failed to start');
      expect(result.current.isRunning).toBe(false);
    });
  });

  describe('stopSession', () => {
    it('should stop session and update state', async () => {
      const mockResponse = {
        status: 'stopped' as const,
        session_id: 'session-123',
        stopped_at: '2026-03-02T18:00:00Z',
        final_portfolio: {
          cash: 10000,
          positions: {},
          total_value: 10500,
          pnl: 500,
          pnl_percent: 5,
          buying_power: 10000,
        },
        total_return: 500,
        total_return_percent: 5,
      };
      vi.mocked(api.paperTradingApi.stopSession).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => usePaperTradingStore());

      await act(async () => {
        await result.current.stopSession();
      });

      expect(result.current.isRunning).toBe(false);
      expect(result.current.portfolio?.pnl).toBe(500);
    });
  });

  describe('fetchStatus', () => {
    it('should fetch and store session status', async () => {
      const mockStatus = {
        is_running: true,
        session_id: 'session-123',
        portfolio: {
          cash: 9000,
          positions: {},
          total_value: 10000,
          pnl: 0,
          pnl_percent: 0,
          buying_power: 9000,
        },
        stats: {
          total_trades: 10,
          buy_trades: 6,
          sell_trades: 4,
          avg_trade_value: 1000,
          avg_profit_loss: 50,
          win_rate: 60,
          uptime_seconds: 3600,
        },
        trades: [],
      };
      vi.mocked(api.paperTradingApi.getSessionStatus).mockResolvedValue(mockStatus);

      const { result } = renderHook(() => usePaperTradingStore());

      await act(async () => {
        await result.current.fetchStatus();
      });

      expect(result.current.isRunning).toBe(true);
      expect(result.current.portfolio?.total_value).toBe(10000);
      expect(result.current.stats?.total_trades).toBe(10);
    });
  });

  describe('addTrade', () => {
    it('should add trade to the beginning of trades array', () => {
      const { result } = renderHook(() => usePaperTradingStore());

      const trade1 = {
        id: 'trade-1',
        timestamp: '2026-03-02T10:00:00Z',
        symbol: 'BTC/EUR',
        side: 'buy' as const,
        qty: 0.1,
        price: 50000,
        value: 5000,
        agent: 'MomentumAgent',
        exchange: 'Bitvavo',
      };

      act(() => {
        result.current.addTrade(trade1);
      });

      expect(result.current.trades).toHaveLength(1);
      expect(result.current.trades[0].id).toBe('trade-1');
    });

    it('should keep only last 50 trades', () => {
      const { result } = renderHook(() => usePaperTradingStore());

      act(() => {
        for (let i = 0; i < 55; i++) {
          result.current.addTrade({
            id: `trade-${i}`,
            timestamp: '2026-03-02T10:00:00Z',
            symbol: 'BTC/EUR',
            side: 'buy',
            qty: 0.1,
            price: 50000,
            value: 5000,
            agent: 'MomentumAgent',
            exchange: 'Bitvavo',
          });
        }
      });

      expect(result.current.trades).toHaveLength(50);
      expect(result.current.trades[0].id).toBe('trade-54'); // Most recent
    });
  });

  describe('selectors', () => {
    it('should select portfolio value', () => {
      const state = usePaperTradingStore.getState();
      state.portfolio = {
        cash: 5000,
        positions: {},
        total_value: 15000,
        pnl: 0,
        pnl_percent: 0,
        buying_power: 5000,
      };

      expect(selectPortfolioValue(state)).toBe(15000);
    });

    it('should select portfolio P&L', () => {
      const state = usePaperTradingStore.getState();
      state.portfolio = {
        cash: 5000,
        positions: {},
        total_value: 15000,
        pnl: 500,
        pnl_percent: 3.33,
        buying_power: 5000,
      };

      expect(selectPortfolioPnl(state)).toBe(500);
      expect(selectPortfolioPnlPercent(state)).toBe(3.33);
    });

    it('should select active positions count', () => {
      const state = usePaperTradingStore.getState();
      state.portfolio = {
        cash: 5000,
        positions: {
          'BTC/EUR': {
            symbol: 'BTC/EUR',
            quantity: 0.1,
            entry_price: 50000,
            current_price: 52000,
            market_value: 5200,
            unrealized_pnl: 200,
            unrealized_pnl_percent: 4,
          },
        },
        total_value: 10200,
        pnl: 200,
        pnl_percent: 2,
        buying_power: 5000,
      };

      expect(selectActivePositions(state)).toBe(1);
    });

    it('should count buy and sell trades', () => {
      const state = usePaperTradingStore.getState();
      state.trades = [
        { id: '1', symbol: 'BTC/EUR', side: 'buy' } as any,
        { id: '2', symbol: 'ETH/EUR', side: 'buy' } as any,
        { id: '3', symbol: 'BTC/EUR', side: 'sell' } as any,
      ];

      expect(selectTradeCount(state)).toBe(3);
      expect(selectBuyTrades(state)).toBe(2);
      expect(selectSellTrades(state)).toBe(1);
    });
  });
});
