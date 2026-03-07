/**
 * Paper Trading Store
 * 
 * Central state management for paper trading functionality.
 * 100% real data from backend - no mock data.
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import {
  paperTradingApi,
  type Trade,
  type Portfolio,
  type SessionStats,
  type PaperTradingSession,
  type StartSessionRequest,
} from '@/lib/api/paper-trading';

// ============================================================================
// STATE INTERFACE
// ============================================================================

interface PaperTradingState {
  // Session state
  sessionId: string | null;
  isRunning: boolean;
  startedAt: string | null;
  config: {
    duration: number;
    capital: number;
  } | null;
  
  // Data
  portfolio: Portfolio | null;
  trades: Trade[];
  stats: SessionStats | null;
  lastUpdated: string | null;
  
  // Loading states
  isLoading: boolean;
  isStarting: boolean;
  isStopping: boolean;
  error: string | null;
  
  // Actions
  startSession: (config: StartSessionRequest) => Promise<void>;
  stopSession: () => Promise<void>;
  fetchStatus: () => Promise<void>;
  fetchPortfolio: () => Promise<void>;
  fetchTrades: () => Promise<void>;
  addTrade: (trade: Trade) => void;
  updatePortfolio: (portfolio: Portfolio) => void;
  updateStats: (stats: SessionStats) => void;
  clearError: () => void;
  reset: () => void;
}

// ============================================================================
// INITIAL STATE
// ============================================================================

const initialState = {
  sessionId: null,
  isRunning: false,
  startedAt: null,
  config: null,
  portfolio: null,
  trades: [],
  stats: null,
  lastUpdated: null,
  isLoading: false,
  isStarting: false,
  isStopping: false,
  error: null,
};

// ============================================================================
// STORE
// ============================================================================

export const usePaperTradingStore = create<PaperTradingState>()(
  devtools(
    (set, get) => ({
      ...initialState,

      /**
       * Start a new paper trading session
       */
      startSession: async (config) => {
        set({ isStarting: true, error: null });
        
        try {
          const response = await paperTradingApi.startSession(config);
          
          set({
            sessionId: response.session_id,
            isRunning: true,
            startedAt: response.started_at,
            config,
            isStarting: false,
            trades: [],
            error: null,
          });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Failed to start session';
          set({ error: message, isStarting: false });
          throw err;
        }
      },

      /**
       * Stop the current session
       */
      stopSession: async () => {
        set({ isStopping: true, error: null });
        
        try {
          const response = await paperTradingApi.stopSession();
          
          set({
            isRunning: false,
            isStopping: false,
            portfolio: response.final_portfolio,
            error: null,
          });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Failed to stop session';
          set({ error: message, isStopping: false });
          throw err;
        }
      },

      /**
       * Fetch current session status
       */
      fetchStatus: async () => {
        const isFirstLoad = !get().sessionId;
        set({ isLoading: isFirstLoad, error: null });
        
        try {
          const status = await paperTradingApi.getSessionStatus();
          
          set({
            isRunning: status.is_running,
            sessionId: status.session_id || null,
            portfolio: status.portfolio || null,
            stats: status.stats || null,
            trades: status.trades || [],
            lastUpdated: new Date().toISOString(),
            isLoading: false,
            error: null,
          });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Failed to fetch status';
          set({ error: message, isLoading: false });
        }
      },

      /**
       * Fetch portfolio data
       */
      fetchPortfolio: async () => {
        try {
          const portfolio = await paperTradingApi.getPortfolio();
          set({ portfolio, error: null });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Failed to fetch portfolio';
          set({ error: message });
        }
      },

      /**
       * Fetch trade history
       */
      fetchTrades: async () => {
        try {
          const trades = await paperTradingApi.getTradeHistory(50);
          set({ trades, error: null });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Failed to fetch trades';
          set({ error: message });
        }
      },

      /**
       * Add a new trade (from WebSocket)
       */
      addTrade: (trade) => {
        set((state) => ({
          trades: [trade, ...state.trades].slice(0, 50),
        }));
      },

      /**
       * Update portfolio (from WebSocket)
       */
      updatePortfolio: (portfolio) => {
        set({ portfolio, lastUpdated: new Date().toISOString() });
      },

      /**
       * Update stats (from WebSocket)
       */
      updateStats: (stats) => {
        set({ stats, lastUpdated: new Date().toISOString() });
      },

      /**
       * Clear error state
       */
      clearError: () => {
        set({ error: null });
      },

      /**
       * Reset store to initial state
       */
      reset: () => {
        set(initialState);
      },
    }),
    { name: 'paper-trading-store' }
  )
);

// ============================================================================
// SELECTORS
// ============================================================================

export const selectPortfolioValue = (state: PaperTradingState): number => {
  return state.portfolio?.total_value || 0;
};

export const selectPortfolioPnl = (state: PaperTradingState): number => {
  return state.portfolio?.pnl || 0;
};

export const selectPortfolioPnlPercent = (state: PaperTradingState): number => {
  return state.portfolio?.pnl_percent || 0;
};

export const selectActivePositions = (state: PaperTradingState): number => {
  return state.portfolio ? Object.keys(state.portfolio.positions).length : 0;
};

export const selectTradeCount = (state: PaperTradingState): number => {
  return state.trades.length;
};

export const selectBuyTrades = (state: PaperTradingState): number => {
  return state.trades.filter(t => t.side === 'buy').length;
};

export const selectSellTrades = (state: PaperTradingState): number => {
  return state.trades.filter(t => t.side === 'sell').length;
};

export default usePaperTradingStore;
