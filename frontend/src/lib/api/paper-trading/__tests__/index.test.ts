/**
 * Paper Trading API Tests
 * 
 * Tests for paper trading API client.
 * Follows TDD: Red-Green-Refactor cycle.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import api from '../../api';
import {
  paperTradingApi,
  startSession,
  stopSession,
  getSessionStatus,
  getPortfolio,
  getTradeHistory,
  type Trade,
  type Portfolio,
  type SessionStats,
} from '../index';

// Mock the api instance
vi.mock('../../api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('Paper Trading API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('startSession', () => {
    it('should start a paper trading session with given config', async () => {
      const mockResponse = {
        data: {
          status: 'started',
          session_id: 'test-session-123',
          started_at: '2026-03-02T10:00:00Z',
        },
      };
      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const config = { duration: 8, capital: 10000 };
      const result = await startSession(config);

      expect(api.post).toHaveBeenCalledWith('/paper-trading/start', config);
      expect(result.status).toBe('started');
      expect(result.session_id).toBe('test-session-123');
    });

    it('should throw error when start fails', async () => {
      vi.mocked(api.post).mockRejectedValue(new Error('Server error'));

      await expect(startSession({ duration: 8, capital: 10000 }))
        .rejects.toThrow('Server error');
    });
  });

  describe('stopSession', () => {
    it('should stop the current session and return final results', async () => {
      const mockResponse = {
        data: {
          status: 'stopped',
          session_id: 'test-session-123',
          stopped_at: '2026-03-02T18:00:00Z',
          final_portfolio: {
            cash: 9500,
            positions: {},
            total_value: 10500,
            pnl: 500,
            pnl_percent: 5,
          },
          total_return: 500,
          total_return_percent: 5,
        },
      };
      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await stopSession();

      expect(api.post).toHaveBeenCalledWith('/paper-trading/stop');
      expect(result.status).toBe('stopped');
      expect(result.total_return).toBe(500);
    });
  });

  describe('getSessionStatus', () => {
    it('should return current session status with portfolio', async () => {
      const mockStatus = {
        data: {
          is_running: true,
          session_id: 'test-session-123',
          portfolio: {
            cash: 9000,
            positions: {
              'BTC/EUR': {
                symbol: 'BTC/EUR',
                quantity: 0.1,
                entry_price: 50000,
                current_price: 51000,
                market_value: 5100,
                unrealized_pnl: 100,
                unrealized_pnl_percent: 2,
              },
            },
            total_value: 10000,
            pnl: 0,
            pnl_percent: 0,
          },
          stats: {
            total_trades: 5,
            buy_trades: 3,
            sell_trades: 2,
            avg_trade_value: 1000,
            avg_profit_loss: 50,
            win_rate: 60,
            uptime_seconds: 3600,
          },
          trades: [],
        },
      };
      vi.mocked(api.get).mockResolvedValue(mockStatus);

      const result = await getSessionStatus();

      expect(api.get).toHaveBeenCalledWith('/paper-trading/status');
      expect(result.is_running).toBe(true);
      expect(result.portfolio?.positions['BTC/EUR']).toBeDefined();
    });

    it('should return inactive status when no session running', async () => {
      const mockStatus = {
        data: {
          is_running: false,
        },
      };
      vi.mocked(api.get).mockResolvedValue(mockStatus);

      const result = await getSessionStatus();

      expect(result.is_running).toBe(false);
    });
  });

  describe('getPortfolio', () => {
    it('should return current portfolio with positions', async () => {
      const mockPortfolio: Portfolio = {
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
          'ETH/EUR': {
            symbol: 'ETH/EUR',
            quantity: 1,
            entry_price: 3000,
            current_price: 3100,
            market_value: 3100,
            unrealized_pnl: 100,
            unrealized_pnl_percent: 3.33,
          },
        },
        total_value: 10300,
        pnl: 300,
        pnl_percent: 3,
        buying_power: 5000,
      };
      vi.mocked(api.get).mockResolvedValue({ data: mockPortfolio });

      const result = await getPortfolio();

      expect(result.total_value).toBe(10300);
      expect(Object.keys(result.positions)).toHaveLength(2);
    });
  });

  describe('getTradeHistory', () => {
    it('should return trade history with limit', async () => {
      const mockTrades: Trade[] = [
        {
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
        {
          id: 'trade-2',
          timestamp: '2026-03-02T11:00:00Z',
          symbol: 'ETH/EUR',
          side: 'buy',
          qty: 1,
          price: 3000,
          value: 3000,
          agent: 'MeanReversionAgent',
          exchange: 'Bitvavo',
        },
      ];
      vi.mocked(api.get).mockResolvedValue({ data: mockTrades });

      const result = await getTradeHistory(50);

      expect(api.get).toHaveBeenCalledWith('/paper-trading/trades', {
        params: { limit: 50 },
      });
      expect(result).toHaveLength(2);
      expect(result[0].symbol).toBe('BTC/EUR');
    });
  });

  describe('paperTradingApi object', () => {
    it('should export all API methods', () => {
      expect(paperTradingApi.startSession).toBeDefined();
      expect(paperTradingApi.stopSession).toBeDefined();
      expect(paperTradingApi.getSessionStatus).toBeDefined();
      expect(paperTradingApi.getSessionStats).toBeDefined();
      expect(paperTradingApi.getPortfolio).toBeDefined();
      expect(paperTradingApi.getTradeHistory).toBeDefined();
      expect(paperTradingApi.getAgentDecisions).toBeDefined();
    });
  });
});
