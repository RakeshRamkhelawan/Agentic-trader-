/**
 * App Store – connected to real backend APIs.
 * All trading data is fetched from the backend; no mock data.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  marketsApi,
  ordersApi,
  portfolioApi,
  navagrahaApi,
  oodaApi,
  agentsApi,
} from '@/lib/api';
import type { Asset, Holding, Order, TradeHistory, AgentStrategy } from '@/lib/api';

export interface AppUser {
  id: string;
  email: string;
  displayName: string;
  avatar?: string;
}

interface AppState {
  // User
  user: AppUser | null;
  setUser: (user: AppUser | null) => void;

  // UI State
  sidebarExpanded: boolean;
  toggleSidebar: () => void;
  currentPage: string;
  setCurrentPage: (page: string) => void;

  // Trading
  selectedSymbol: string;
  setSelectedSymbol: (symbol: string) => void;
  timeframe: string;
  setTimeframe: (timeframe: string) => void;

  // Assets
  assets: Asset[];
  isLoadingAssets: boolean;
  fetchAssets: () => Promise<void>;
  updateAssetPrice: (symbol: string, price: number, change24h: number) => void;
  
  // Top Movers (calculated from assets)
  topGainer: Asset | null;
  topLoser: Asset | null;
  getTopMovers: () => { gainers: Asset[]; losers: Asset[] };
  
  // Chart auto-selection
  chartSymbol: string;
  setChartSymbol: (symbol: string) => void;
  autoSelectTopGainer: () => void;

  // Holdings
  holdings: Holding[];
  isLoadingHoldings: boolean;
  fetchHoldings: () => Promise<void>;

  // Orders
  orders: Order[];
  isLoadingOrders: boolean;
  fetchOrders: () => Promise<void>;
  addOrder: (order: Order) => void;
  cancelOrder: (orderId: string) => Promise<void>;

  // Trade History
  tradeHistory: TradeHistory[];
  isLoadingHistory: boolean;
  fetchTradeHistory: () => Promise<void>;
  addTrade: (trade: TradeHistory) => void;

  // Portfolio Performance
  portfolioValue: number;
  portfolioPnl: number;
  portfolioPnlPercent: number;
  dailyPnl: number;
  availableBalance: number;
  isLoadingPortfolio: boolean;
  fetchPortfolio: () => Promise<void>;

  // Agents Status
  agentsStatus: AgentStrategy[];
  agentsCoherence: number;
  isLoadingAgents: boolean;
  fetchAgentsStatus: () => Promise<void>;

  // Consciousness State (Navagraha)
  navagrahaState: {
    current_dasha: string;
    guna_distribution: { sattva: number; rajas: number; tamas: number };
    trading_gate_open: boolean;
    consciousness_level: number;
  } | null;
  isLoadingNavagraha: boolean;
  fetchNavagrahaState: () => Promise<void>;

  // OODA State
  oodaState: {
    phase: string;
    cycle_id: string;
    coherence: number;
    confidence: number;
    timestamp: string;
  } | null;
  isLoadingOoda: boolean;
  fetchOodaState: () => Promise<void>;

  // Bulk initializer – called once on login/app start
  initializeData: () => Promise<void>;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // User
      user: null,
      setUser: (user) => set({ user }),

      // UI State
      sidebarExpanded: false,
      toggleSidebar: () => set((state) => ({ sidebarExpanded: !state.sidebarExpanded })),
      currentPage: 'dashboard',
      setCurrentPage: (page) => set({ currentPage: page }),

      // Trading
      selectedSymbol: 'BTC/EUR',
      setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
      timeframe: '1h',
      setTimeframe: (timeframe) => set({ timeframe }),
      
      // Chart symbol (for TradingChart - auto-selected from top gainer)
      chartSymbol: 'BTC/EUR',
      setChartSymbol: (symbol) => set({ chartSymbol: symbol }),
      autoSelectTopGainer: () => {
        const { assets, chartSymbol } = get();
        if (assets.length === 0) return;
        
        // Sort by change24h descending
        const sorted = [...assets].sort((a, b) => (b.change24h || 0) - (a.change24h || 0));
        const topGainer = sorted[0];
        
        // Only update if different and we haven't manually selected
        if (topGainer && topGainer.symbol !== chartSymbol) {
          set({ chartSymbol: topGainer.symbol });
        }
      },

      // Assets
      assets: [],
      isLoadingAssets: false,
      topGainer: null,
      topLoser: null,
      fetchAssets: async () => {
        set({ isLoadingAssets: true });
        try {
          const assets = await marketsApi.getAssets();
          
          // Calculate top gainers/losers
          const sorted = [...assets].sort((a, b) => (b.change24h || 0) - (a.change24h || 0));
          const topGainer = sorted.length > 0 ? sorted[0] : null;
          const topLoser = sorted.length > 0 ? sorted[sorted.length - 1] : null;
          
          set({ 
            assets, 
            topGainer,
            topLoser,
            isLoadingAssets: false 
          });
          
          // Auto-select top gainer for chart if not manually set
          const state = get();
          if (state.chartSymbol === 'BTC/EUR' && topGainer) {
            set({ chartSymbol: topGainer.symbol });
          }
        } catch (error) {
          console.error('Failed to fetch assets:', error);
          set({ isLoadingAssets: false });
        }
      },
      getTopMovers: () => {
        const { assets } = get();
        const sorted = [...assets].sort((a, b) => (b.change24h || 0) - (a.change24h || 0));
        return {
          gainers: sorted.slice(0, 5),
          losers: sorted.slice(-5).reverse(),
        };
      },
      updateAssetPrice: (symbol, price, change24h) =>
        set((state) => ({
          assets: state.assets.map((a) =>
            a.symbol === symbol ? { ...a, price, change24h } : a
          ),
        })),

      // Holdings
      holdings: [],
      isLoadingHoldings: false,
      fetchHoldings: async () => {
        set({ isLoadingHoldings: true });
        try {
          const holdings = await portfolioApi.getHoldings();
          set({ holdings, isLoadingHoldings: false });
        } catch (error) {
          console.error('Failed to fetch holdings:', error);
          set({ isLoadingHoldings: false });
        }
      },

      // Orders
      orders: [],
      isLoadingOrders: false,
      fetchOrders: async () => {
        set({ isLoadingOrders: true });
        try {
          const orders = await ordersApi.getOrders();
          set({ orders, isLoadingOrders: false });
        } catch (error) {
          console.error('Failed to fetch orders:', error);
          set({ isLoadingOrders: false });
        }
      },
      addOrder: (order) => set((state) => ({ orders: [order, ...state.orders] })),
      cancelOrder: async (orderId) => {
        // Optimistic update first
        set((state) => ({
          orders: state.orders.map((o) =>
            o.id === orderId ? { ...o, status: 'cancelled' as const } : o
          ),
        }));
        try {
          await ordersApi.cancelOrder(orderId);
        } catch (error) {
          console.error('Failed to cancel order:', error);
          // Revert optimistic update on error
          await get().fetchOrders();
        }
      },

      // Trade History
      tradeHistory: [],
      isLoadingHistory: false,
      fetchTradeHistory: async () => {
        set({ isLoadingHistory: true });
        try {
          const history = await portfolioApi.getHistory();
          set({ tradeHistory: history, isLoadingHistory: false });
        } catch (error) {
          console.error('Failed to fetch trade history:', error);
          set({ isLoadingHistory: false });
        }
      },
      addTrade: (trade) => set((state) => ({ tradeHistory: [trade, ...state.tradeHistory] })),

      // Portfolio Performance
      portfolioValue: 0,
      portfolioPnl: 0,
      portfolioPnlPercent: 0,
      dailyPnl: 0,
      availableBalance: 0,
      isLoadingPortfolio: false,
      fetchPortfolio: async () => {
        set({ isLoadingPortfolio: true });
        try {
          const performance = await portfolioApi.getPerformance();
          set({
            portfolioValue: performance.totalValue,
            portfolioPnl: performance.totalPnl,
            portfolioPnlPercent: performance.totalPnlPercent,
            dailyPnl: performance.dailyPnl,
            availableBalance: performance.availableBalance,
            isLoadingPortfolio: false,
          });
        } catch (error) {
          console.error('Failed to fetch portfolio:', error);
          set({ isLoadingPortfolio: false });
        }
      },

      // Agents Status
      agentsStatus: [],
      agentsCoherence: 0,
      isLoadingAgents: false,
      fetchAgentsStatus: async () => {
        set({ isLoadingAgents: true });
        try {
          const data = await agentsApi.getStatus();
          // Normalize agents map into array
          const agentsList: AgentStrategy[] = Object.entries(data.agents ?? {}).map(
            ([id, a]: [string, any]) => ({
              id,
              name: a.type ?? id,
              type: a.type ?? 'agent',
              status: a.is_active ? 'running' : 'paused',
              performance: Number(a.prana ?? 0),
              trades: Number(a.state?.total_trades ?? 0),
              prana: Number(a.prana ?? 0),
            })
          );
          const coherence =
            data.orchestrator_state?.global_coherence ?? 0;
          set({ agentsStatus: agentsList, agentsCoherence: coherence, isLoadingAgents: false });
        } catch (error) {
          console.error('Failed to fetch agents status:', error);
          set({ isLoadingAgents: false });
        }
      },

      // Consciousness State
      navagrahaState: null,
      isLoadingNavagraha: false,
      fetchNavagrahaState: async () => {
        set({ isLoadingNavagraha: true });
        try {
          const state = await navagrahaApi.getCurrentState();
          set({ navagrahaState: state, isLoadingNavagraha: false });
        } catch (error) {
          console.error('Failed to fetch navagraha state:', error);
          set({ isLoadingNavagraha: false });
        }
      },

      // OODA State
      oodaState: null,
      isLoadingOoda: false,
      fetchOodaState: async () => {
        set({ isLoadingOoda: true });
        try {
          const state = await oodaApi.getCurrentCycle();
          set({ oodaState: state, isLoadingOoda: false });
        } catch (error) {
          console.error('Failed to fetch OODA state:', error);
          set({ isLoadingOoda: false });
        }
      },

      // Bulk initializer
      initializeData: async () => {
        const { fetchAssets, fetchPortfolio, fetchOrders, fetchHoldings, fetchTradeHistory, fetchAgentsStatus } =
          get();
        await Promise.allSettled([
          fetchAssets(),
          fetchPortfolio(),
          fetchOrders(),
          fetchHoldings(),
          fetchTradeHistory(),
          fetchAgentsStatus(),
        ]);
      },
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({
        sidebarExpanded: state.sidebarExpanded,
        selectedSymbol: state.selectedSymbol,
        timeframe: state.timeframe,
      }),
    }
  )
);
