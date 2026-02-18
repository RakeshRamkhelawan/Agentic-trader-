/**
 * Real API Client for Agentic Trader Platform
 * 
 * Uses the backend API (no mocks).
 * Integrates with the existing Next.js frontend.
 */

import axios, { AxiosError, AxiosInstance } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Response interceptor - handle 401
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// AUTH API
// ============================================================================

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    tenant_id: string;
    role: string;
    full_name: string | null;
  };
}

export const authApi = {
  register: async (data: { email: string; password: string; full_name: string }) => {
    const response = await api.post<AuthResponse>('/auth/register', data);
    return response.data;
  },

  login: async (data: { email: string; password: string }) => {
    const response = await api.post<AuthResponse>('/auth/login', data);
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
  },

  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// ============================================================================
// KYC API (Implemented but disabled by default)
// ============================================================================

export interface KYCData {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  nationality: string;
  phone_number: string;
  street_address: string;
  city: string;
  postal_code: string;
  country: string;
  id_type: 'passport' | 'drivers_license' | 'national_id';
  id_number: string;
  occupation: string;
  employment_status: string;
  annual_income: string;
  source_of_funds: string;
}

export interface KYCResponse {
  status: 'not_started' | 'in_progress' | 'pending_review' | 'verified' | 'rejected';
  submitted_at?: string;
  reviewed_at?: string;
  rejection_reason?: string;
  required: boolean;
  enabled: boolean;
}

export const kycApi = {
  getStatus: async (): Promise<KYCResponse> => {
    const response = await api.get<KYCResponse>('/kyc/status');
    return response.data;
  },

  submit: async (data: KYCData) => {
    const response = await api.post('/kyc/submit', data);
    return response.data;
  },

  uploadDocuments: async (files: { id_front?: File; id_back?: File; selfie?: File }) => {
    const formData = new FormData();
    if (files.id_front) formData.append('id_front', files.id_front);
    if (files.id_back) formData.append('id_back', files.id_back);
    if (files.selfie) formData.append('selfie', files.selfie);

    const response = await api.post('/kyc/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  isRequired: async () => {
    const response = await api.get('/kyc/required');
    return response.data;
  },
};

export default api;
