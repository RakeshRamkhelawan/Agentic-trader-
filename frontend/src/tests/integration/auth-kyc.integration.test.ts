/**
 * @vitest-environment node
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { authApi } from '../../lib/api/auth-api';
import { kycApi, KYCStatus } from '../../lib/api/kyc-api';
import { apiClient } from '../../lib/api-client';

describe('Auth & KYC Integration', () => {
    const testEmail = `test-${Date.now()}@example.com`;
    const testPassword = 'password123';
    const testFullName = 'Test User';
    let accessToken: string;

    // Increase timeout for integration tests
    const timeout = 30000;

    it('should register a new user successfully', async () => {
        const response = await authApi.register({
            email: testEmail,
            password: testPassword,
            full_name: testFullName
        });

        expect(response.access_token).toBeDefined();
        expect(response.user.email).toBe(testEmail);
        expect(response.user.full_name).toBe(testFullName);
        
        accessToken = response.access_token;
        // Inject token manually for node env
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
    }, timeout);

    it('should login with the registered user', async () => {
        const response = await authApi.login({
            email: testEmail,
            password: testPassword
        });

        expect(response.access_token).toBeDefined();
        expect(response.user.email).toBe(testEmail);
        
        accessToken = response.access_token;
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
    }, timeout);

    it('should fetch current user info (me)', async () => {
        const user = await authApi.me();
        expect(user.email).toBe(testEmail);
        expect(user.full_name).toBeDefined();
    }, timeout);

    it('should reject login with wrong password', async () => {
        // Clear auth header to test negative case
        const oldAuth = apiClient.defaults.headers.common['Authorization'];
        delete apiClient.defaults.headers.common['Authorization'];
        
        await expect(authApi.login({
            email: testEmail,
            password: 'wrongpassword'
        })).rejects.toThrow('Invalid email or password');
        
        apiClient.defaults.headers.common['Authorization'] = oldAuth;
    }, timeout);

    it('should get initial KYC status', async () => {
        const status = await kycApi.getStatus();
        expect(status).toHaveProperty('status');
        expect(status).toHaveProperty('enabled');
    }, timeout);

    it('should submit KYC data', async () => {
        const kycData = {
            first_name: 'Test',
            last_name: 'User',
            date_of_birth: '1990-01-01',
            nationality: 'US',
            phone_number: '+1234567890',
            street_address: '123 Test St',
            city: 'Test City',
            postal_code: '12345',
            country: 'US',
            id_type: 'passport' as any,
            id_number: 'P12345678',
            occupation: 'Software Engineer',
            employment_status: 'employed' as any,
            annual_income: '50k-100k' as any,
            source_of_funds: 'Salary'
        };

        const response = await kycApi.submit(kycData);
        expect(response.success).toBe(true);
        expect([KYCStatus.PENDING_REVIEW, KYCStatus.VERIFIED]).toContain(response.status);
    }, timeout);
});
