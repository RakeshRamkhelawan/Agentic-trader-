/**
 * Integration Tests for Frontend-Backend API
 * 
 * Tests real API endpoints with the backend server.
 * Run these tests against a running backend.
 */

import { describe, it, expect, beforeAll } from 'vitest';
import { authApi, kycApi } from '@/lib/api/real-api';

describe('Auth API Integration', () => {
  const testEmail = `test-${Date.now()}@example.com`;
  const testPassword = 'TestPassword123!';
  const testName = 'Test User';

  it('should register a new user (happy path)', async () => {
    const response = await authApi.register({
      email: testEmail,
      password: testPassword,
      full_name: testName,
    });

    expect(response).toHaveProperty('access_token');
    expect(response).toHaveProperty('user');
    expect(response.user.email).toBe(testEmail);
    expect(response.token_type).toBe('bearer');
  });

  it('should login with valid credentials (happy path)', async () => {
    const response = await authApi.login({
      email: testEmail,
      password: testPassword,
    });

    expect(response).toHaveProperty('access_token');
    expect(response.user.email).toBe(testEmail);
    
    // Store token for subsequent tests
    localStorage.setItem('access_token', response.access_token);
  });

  it('should reject login with invalid credentials (unhappy path)', async () => {
    await expect(
      authApi.login({
        email: testEmail,
        password: 'wrongpassword',
      })
    ).rejects.toThrow();
  });

  it('should reject duplicate registration (unhappy path)', async () => {
    await expect(
      authApi.register({
        email: testEmail,
        password: testPassword,
        full_name: testName,
      })
    ).rejects.toThrow(/already registered|duplicate/i);
  });

  it('should get current user when authenticated (happy path)', async () => {
    const user = await authApi.getMe();
    
    expect(user).toHaveProperty('id');
    expect(user).toHaveProperty('email');
    expect(user.email).toBe(testEmail);
  });
});

describe('KYC API Integration', () => {
  beforeAll(() => {
    // Ensure we have a token
    const token = localStorage.getItem('access_token');
    if (!token) {
      console.warn('No auth token found, KYC tests may fail');
    }
  });

  it('should return KYC status (happy path)', async () => {
    const status = await kycApi.getStatus();
    
    expect(status).toHaveProperty('status');
    expect(status).toHaveProperty('enabled');
    expect(status).toHaveProperty('required');
    
    // KYC is disabled by default
    expect(status.enabled).toBe(false);
    expect(status.required).toBe(false);
    expect(status.status).toBe('verified');
  });

  it('should accept KYC submission when disabled (happy path)', async () => {
    const kycData = {
      first_name: 'John',
      last_name: 'Doe',
      date_of_birth: '1990-01-01',
      nationality: 'NL',
      phone_number: '+31612345678',
      street_address: 'Test Street 123',
      city: 'Amsterdam',
      postal_code: '1012 AB',
      country: 'NL',
      id_type: 'passport' as const,
      id_number: 'ABC123456',
      occupation: 'Software Engineer',
      employment_status: 'employed' as const,
      annual_income: '50k-100k' as const,
      source_of_funds: 'Salary',
    };

    const response = await kycApi.submit(kycData);
    
    expect(response.success).toBe(true);
    expect(response.status).toBe('verified');
  });

  it('should reject KYC submission with invalid data (unhappy path)', async () => {
    const invalidData = {
      first_name: '', // Empty - should fail
      last_name: 'Doe',
      date_of_birth: 'invalid-date',
      nationality: 'NL',
      phone_number: '+31612345678',
      street_address: 'Test Street 123',
      city: 'Amsterdam',
      postal_code: '1012 AB',
      country: 'NL',
      id_type: 'passport' as const,
      id_number: 'ABC123456',
      occupation: 'Software Engineer',
      employment_status: 'employed' as const,
      annual_income: '50k-100k' as const,
      source_of_funds: 'Salary',
    };

    await expect(kycApi.submit(invalidData as any)).rejects.toThrow();
  });

  it('should check if KYC is required (happy path)', async () => {
    const result = await kycApi.isRequired();
    
    expect(result).toHaveProperty('required');
    expect(result).toHaveProperty('enabled');
    expect(result).toHaveProperty('status');
    
    // Should not be required when disabled
    expect(result.required).toBe(false);
  });
});
