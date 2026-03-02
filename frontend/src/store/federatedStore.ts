/**
 * Federated Triad Store - Real Data from Backend
 * 
 * This store provides real-time access to the Federated Triad system state
 * including councils, coherence metrics, Chitta nodes, and Buddhi decisions.
 * 
 * NO MOCK DATA - All data comes from /api/v1/federated/state
 */

import { create } from 'zustand';
import { federatedApi, type FederatedState, type CouncilView, type ChittaNode, type BuddhiDecision } from '@/lib/api';

interface CoherenceMetrics {
  total: number;
  harmony: number;
  performance: number;
  chitta_health: number;
  deliberation_quality: number;
  buddhi_clarity: number;
}

interface DeliberationStep {
  iteration: number;
  council: string;
  perspective: string;
  confidence: number;
}

interface FederatedStoreState {
  // Data from backend
  coherence: CoherenceMetrics | null;
  councils: CouncilView[];
  chittaNodes: ChittaNode[];
  latestDecision: BuddhiDecision | null;
  deliberationSteps: DeliberationStep[];
  
  // Loading and error states
  isLoading: boolean;
  isRefreshing: boolean;
  error: string | null;
  lastUpdated: Date | null;
  
  // Actions
  fetchState: () => Promise<void>;
  refresh: () => Promise<void>;
  clearError: () => void;
}

export const useFederatedStore = create<FederatedStoreState>()((set, get) => ({
  // Initial state - all null/empty, no mock data
  coherence: null,
  councils: [],
  chittaNodes: [],
  latestDecision: null,
  deliberationSteps: [],
  isLoading: false,
  isRefreshing: false,
  error: null,
  lastUpdated: null,

  /**
   * Fetch federated state from backend
   * This is the ONLY source of truth - no mock data fallback
   */
  fetchState: async () => {
    const isFirstLoad = !get().lastUpdated;
    set({ 
      isLoading: isFirstLoad, 
      isRefreshing: !isFirstLoad,
      error: null 
    });

    try {
      const state = await federatedApi.getState();
      
      set({
        coherence: state.coherence,
        councils: state.councils,
        chittaNodes: state.chitta.nodes,
        latestDecision: state.latest_decision,
        deliberationSteps: state.deliberation_steps,
        lastUpdated: new Date(),
        isLoading: false,
        isRefreshing: false,
        error: null,
      });
    } catch (err) {
      console.error('[FederatedStore] Failed to fetch state:', err);
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch federated state',
        isLoading: false,
        isRefreshing: false,
      });
    }
  },

  /**
   * Refresh data (for manual refresh or polling)
   */
  refresh: async () => {
    await get().fetchState();
  },

  /**
   * Clear any error state
   */
  clearError: () => {
    set({ error: null });
  },
}));

export default useFederatedStore;
