/**
 * Authentication Service
 * 
 * Handles all authentication-related API calls.
 * Manages tokens securely via httpOnly cookies or in-memory storage.
 */

import { api } from '@/lib/api';
import type { 
  User, 
  LoginCredentials, 
  RegisterData, 
  AuthTokens,
  KYCData,
  KYCResponse 
} from '@/types';

interface LoginResponse {
  user: User;
  access_token: string;
  expires_at?: number;
}

interface RegisterResponse {
  user: User;
  access_token: string;
  expires_at?: number;
}

/**
 * Login user with email and password
 */
export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('/auth/login', credentials);
  return response.data;
}

/**
 * Register new user
 */
export async function register(data: RegisterData): Promise<RegisterResponse> {
  const response = await api.post<RegisterResponse>('/auth/register', {
    email: data.email,
    password: data.password,
    full_name: `${data.firstName} ${data.lastName}`.trim(),
  });
  return response.data;
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
  await api.post('/auth/logout');
}

/**
 * Get current user profile
 */
export async function getCurrentUser(): Promise<User> {
  const response = await api.get<User>('/auth/me');
  return response.data;
}

/**
 * Refresh access token
 */
export async function refreshToken(): Promise<AuthTokens> {
  const response = await api.post<AuthTokens>('/auth/refresh');
  return response.data;
}

/**
 * Request password reset
 */
export async function requestPasswordReset(email: string): Promise<void> {
  await api.post('/auth/forgot-password', { email });
}

/**
 * Reset password with token
 */
export async function resetPassword(token: string, newPassword: string): Promise<void> {
  await api.post('/auth/reset-password', { token, password: newPassword });
}

// ============================================================================
// KYC Services
// ============================================================================

/**
 * Get KYC status for current user
 */
export async function getKYCStatus(): Promise<KYCResponse> {
  const response = await api.get<KYCResponse>('/kyc/status');
  return response.data;
}

/**
 * Submit KYC data
 */
export async function submitKYC(data: KYCData): Promise<KYCResponse> {
  const response = await api.post<KYCResponse>('/kyc/submit', data);
  return response.data;
}

/**
 * Upload KYC document
 */
export async function uploadKYCDocument(
  file: File,
  documentType: string
): Promise<{ url: string }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);
  
  const response = await api.post<{ url: string }>('/kyc/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}
