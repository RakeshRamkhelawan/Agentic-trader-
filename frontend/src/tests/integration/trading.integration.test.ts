
import { describe, it, expect, beforeAll } from 'vitest';
import { authApi } from '../../lib/api/auth-api';
import { tradingPortfolioApi } from '../../lib/api/trading-portfolio-api';
import { apiClient } from '../../lib/api-client';

/**
 * @vitest-environment node
 */

describe('Trading & Portfolio Integration', () => {
    let token: string;
    const testEmail = `trading_test_${Date.now()}@example.com`;
    const testPassword = 'Password123!';

    beforeAll(async () => {
        // Register and login to get token
        await authApi.register({ email: testEmail, password: testPassword });
        const loginRes = await authApi.login({ email: testEmail, password: testPassword });
        token = loginRes.access_token;
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }, 30000);

    it('should list available assets', async () => {
        const assets = await tradingPortfolioApi.getAssets();
        expect(Array.isArray(assets)).toBe(true);
        if (assets.length > 0) {
            expect(assets[0]).toHaveProperty('symbol');
        }
    });

    it('should get ticker data for BTC/USDT', async () => {
        const ticker = await tradingPortfolioApi.getTicker('BTC/USDT');
        expect(ticker).toHaveProperty('symbol', 'BTC/USDT');
        expect(ticker).toHaveProperty('price');
    });

    it('should fetch portfolio holdings', async () => {
        const portfolio = await tradingPortfolioApi.getPortfolio();
        expect(portfolio).toHaveProperty('total_value');
        expect(portfolio).toHaveProperty('assets');
    });

    it('should create a buy order', async () => {
        const order = await tradingPortfolioApi.createOrder({
            symbol: 'BTC/USDT',
            side: 'buy',
            type: 'market',
            quantity: 0.01
        });
        expect(order).toHaveProperty('id');
        expect(order.status).toBeDefined();
    });

    it('should fetch trade history', async () => {
        const history = await tradingPortfolioApi.getHistory();
        expect(Array.isArray(history)).toBe(true);
    });
});
