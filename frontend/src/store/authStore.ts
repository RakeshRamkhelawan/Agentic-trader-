/**
 * REAL Authentication Store - Connected to Backend API
 * 
 * This store uses the real API client (no mocks).
 * All auth operations go to the backend.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi, kycApi } from '@/lib/api';
import type { KYCData, KYCResponse } from '@/lib/api';

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  displayName: string;
  avatar?: string;
  phone?: string;
  dateOfBirth?: string;
  country?: string;
  createdAt: Date;
}

export interface OnboardingData {
  email: string;
  password: string;
  confirmPassword: string;
  agreedToTerms: boolean;
  agreedToPrivacy: boolean;
  marketingConsent: boolean;
}

interface AuthState {
  // Auth State
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Onboarding State
  onboardingStep: number;
  onboardingData: Partial<OnboardingData>;
  
  // KYC State
  kycData: Partial<KYCData>;
  kycStep: number;
  kycStatus: KYCResponse | null;
  
  // Actions
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  register: (email: string, password: string, firstName: string, lastName: string) => Promise<boolean>;
  fetchCurrentUser: () => Promise<boolean>;
  
  // Onboarding Actions
  setOnboardingStep: (step: number) => void;
  updateOnboardingData: (data: Partial<OnboardingData>) => void;
  completeOnboarding: () => void;
  
  // KYC Actions
  setKYCStep: (step: number) => void;
  updateKYCData: (data: Partial<KYCData>) => void;
  fetchKYCStatus: () => Promise<void>;
  submitKYC: () => Promise<boolean>;
  
  // Reset
  clearError: () => void;
  resetOnboarding: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial State
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      
      onboardingStep: 0,
      onboardingData: {},
      
      kycData: {
        status: 'not_started',
      } as any,
      kycStep: 0,
      kycStatus: null,

      // Login Action - REAL API
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await authApi.login({ email, password });
          
          // Store token
          localStorage.setItem('access_token', response.access_token);
          
          // Create user object from response
          const user: User = {
            id: response.user.id,
            email: response.user.email,
            firstName: response.user.full_name?.split(' ')[0] || '',
            lastName: response.user.full_name?.split(' ').slice(1).join(' ') || '',
            displayName: response.user.full_name || response.user.email,
            createdAt: new Date(),
          };
          
          set({ 
            user, 
            isAuthenticated: true, 
            isLoading: false,
            error: null 
          });
          
          // Fetch KYC status after login
          await get().fetchKYCStatus();
          
          return true;
        } catch (error: any) {
          set({ 
            isLoading: false, 
            error: error.message || 'Invalid email or password' 
          });
          return false;
        }
      },

      // Logout Action - REAL API
      logout: () => {
        authApi.logout();
        set({ 
          user: null, 
          isAuthenticated: false,
          error: null,
          kycStatus: null,
        });
      },

      // Register Action - REAL API
      register: async (email: string, password: string, firstName: string, lastName: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const fullName = `${firstName} ${lastName}`.trim();
          const response = await authApi.register({ 
            email, 
            password, 
            full_name: fullName 
          });
          
          // Store token
          localStorage.setItem('access_token', response.access_token);
          
          // Create user object
          const user: User = {
            id: response.user.id,
            email: response.user.email,
            firstName,
            lastName,
            displayName: fullName,
            createdAt: new Date(),
          };
          
          set({ 
            user, 
            isAuthenticated: true, 
            isLoading: false,
            error: null 
          });
          
          // Fetch KYC status after registration
          await get().fetchKYCStatus();
          
          return true;
        } catch (error: any) {
          set({ 
            isLoading: false, 
            error: error.message || 'Registration failed. Please try again.' 
          });
          return false;
        }
      },

      // Fetch Current User - REAL API
      fetchCurrentUser: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return false;
        }
        
        set({ isLoading: true });
        
        try {
          const userData = await authApi.getMe();
          
          const user: User = {
            id: userData.id,
            email: userData.email,
            firstName: userData.full_name?.split(' ')[0] || '',
            lastName: userData.full_name?.split(' ').slice(1).join(' ') || '',
            displayName: userData.full_name || userData.email,
            createdAt: new Date(),
          };
          
          set({ 
            user, 
            isAuthenticated: true, 
            isLoading: false 
          });
          
          // Also fetch KYC status
          await get().fetchKYCStatus();
          
          return true;
        } catch (error) {
          // Token invalid or expired
          localStorage.removeItem('access_token');
          set({ 
            isAuthenticated: false, 
            user: null, 
            isLoading: false 
          });
          return false;
        }
      },

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

      // KYC Actions - REAL API
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
        set({ isLoading: true, error: null });
        
        try {
          const data = get().kycData as KYCData;
          const response = await kycApi.submit(data);
          
          // Refresh status
          await get().fetchKYCStatus();
          
          set({ isLoading: false });
          return response.success;
        } catch (error: any) {
          set({ 
            isLoading: false, 
            error: error.message || 'KYC submission failed' 
          });
          return false;
        }
      },

      // Reset Actions
      clearError: () => {
        set({ error: null });
      },

      resetOnboarding: () => {
        set({ 
          onboardingStep: 0,
          onboardingData: {},
          kycStep: 0,
          kycData: { status: 'not_started' } as any,
        });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        isAuthenticated: state.isAuthenticated,
        kycData: state.kycData,
        kycStatus: state.kycStatus,
      }),
    }
  )
);
