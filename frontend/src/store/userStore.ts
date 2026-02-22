/**
 * User Store - UI State Only (Not Authentication)
 * 
 * This store manages user-related UI state:
 * - Onboarding flow
 * - KYC progress
 * - User preferences
 * 
 * Authentication is handled by AuthContext (Auth0).
 * This store should NOT be used for auth state.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { kycApi } from '@/lib/api';
import type { KYCData, KYCResponse } from '@/lib/api';

export interface OnboardingData {
  email: string;
  password: string;
  confirmPassword: string;
  agreedToTerms: boolean;
  agreedToPrivacy: boolean;
  marketingConsent: boolean;
}

interface UserState {
  // Onboarding State
  onboardingStep: number;
  onboardingData: Partial<OnboardingData>;
  
  // KYC State
  kycData: Partial<KYCData>;
  kycStep: number;
  kycStatus: KYCResponse | null;
  kycIsLoading: boolean;
  kycError: string | null;
  
  // UI Preferences
  sidebarExpanded: boolean;
  theme: 'dark' | 'light';
  
  // Onboarding Actions
  setOnboardingStep: (step: number) => void;
  updateOnboardingData: (data: Partial<OnboardingData>) => void;
  completeOnboarding: () => void;
  resetOnboarding: () => void;
  
  // KYC Actions
  setKYCStep: (step: number) => void;
  updateKYCData: (data: Partial<KYCData>) => void;
  fetchKYCStatus: () => Promise<void>;
  submitKYC: () => Promise<boolean>;
  clearKYCError: () => void;
  
  // UI Actions
  toggleSidebar: () => void;
  setSidebarExpanded: (expanded: boolean) => void;
  setTheme: (theme: 'dark' | 'light') => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set, get) => ({
      // Initial State
      onboardingStep: 0,
      onboardingData: {},
      
      kycData: {
        status: 'not_started',
      } as any,
      kycStep: 0,
      kycStatus: null,
      kycIsLoading: false,
      kycError: null,
      
      sidebarExpanded: true,
      theme: 'dark',

      // Onboarding Actions
      setOnboardingStep: (step: number) => {
        set({ onboardingStep: step });
      },

      updateOnboardingData: (data: Partial<OnboardingData>) => {
        set(state => ({ 
          onboardingData: { ...state.onboardingData, ...data } 
        }));
      },

      completeOnboarding: () => {
        set({ 
          onboardingStep: 0,
          onboardingData: {} 
        });
      },

      resetOnboarding: () => {
        set({ 
          onboardingStep: 0,
          onboardingData: {},
        });
      },

      // KYC Actions
      setKYCStep: (step: number) => {
        set({ kycStep: step });
      },

      updateKYCData: (data: Partial<KYCData>) => {
        set(state => ({ 
          kycData: { ...state.kycData, ...data } 
        }));
      },

      fetchKYCStatus: async () => {
        try {
          const status = await kycApi.getStatus();
          set({ kycStatus: status });
        } catch (error) {
          console.error('Failed to fetch KYC status:', error);
        }
      },

      submitKYC: async () => {
        set({ kycIsLoading: true, kycError: null });
        
        try {
          const data = get().kycData as KYCData;
          const response = await kycApi.submit(data);
          
          // Refresh status
          await get().fetchKYCStatus();
          
          set({ kycIsLoading: false });
          return response.success;
        } catch (error: any) {
          set({ 
            kycIsLoading: false, 
            kycError: error.message || 'KYC submission failed' 
          });
          return false;
        }
      },

      clearKYCError: () => {
        set({ kycError: null });
      },

      // UI Actions
      toggleSidebar: () => {
        set(state => ({ sidebarExpanded: !state.sidebarExpanded }));
      },

      setSidebarExpanded: (expanded: boolean) => {
        set({ sidebarExpanded: expanded });
      },

      setTheme: (theme: 'dark' | 'light') => {
        set({ theme });
      },
    }),
    {
      name: 'user-storage',
      // Only persist UI state, never auth tokens
      partialize: (state) => ({ 
        kycData: state.kycData,
        kycStatus: state.kycStatus,
        sidebarExpanded: state.sidebarExpanded,
        theme: state.theme,
      }),
    }
  )
);

// Deprecated: useUserStore should be used instead
// This maintains backward compatibility during migration
export const useAuthStore = useUserStore;
