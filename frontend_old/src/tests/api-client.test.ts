import { describe, it, expect, vi, beforeAll, afterAll } from 'vitest';
import axios from 'axios';
import { apiClient } from '../lib/api-client';

describe('Axios API Client', () => {
    it('should have the correct base configuration', () => {
        expect(apiClient.defaults.baseURL).toBeDefined();
        expect(apiClient.interceptors.request).toBeDefined();
        expect(apiClient.interceptors.response).toBeDefined();
    });

    it('should inject Auth token into headers when available', async () => {
        const token = 'test-token';
        localStorage.setItem('access_token', token);
        
        // Mocking a request to see if interceptor adds the header
        const requestConfig = { headers: {} } as any;
        // @ts-ignore - access private interceptors if needed or just test through logic
        const interceptor = (apiClient.interceptors.request as any).handlers[0].fulfilled;
        const result = await interceptor(requestConfig);
        
        expect(result.headers.Authorization).toBe(`Bearer ${token}`);
        localStorage.removeItem('access_token');
    });
});
