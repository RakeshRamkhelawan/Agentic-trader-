"use client"

import { OpenAPI } from './api-client/generated/core/OpenAPI';
import { AnalyticsService } from './api-client/generated/services/AnalyticsService';
import { AuthService } from './api-client/generated/services/AuthService';
import { TradingService } from './api-client/generated/services/TradingService';
import { SettingsService } from './api-client/generated/services/SettingsService';
import { ApprovalsService } from './api-client/generated/services/ApprovalsService';

// Configure the base URL for the generated client
if (typeof window !== 'undefined') {
    // Use relative path to leverage Next.js proxy (next.config.ts rewrites)
    OpenAPI.BASE = '';

    // Delegate token resolution to a global handler that AuthContext will provide.
    // This solves race conditions where the API is called before AuthContext is ready.
    // @ts-ignore
    OpenAPI.TOKEN = async () => {
        const resolver = (window as any)._resolveToken;
        if (resolver) {
            return await resolver();
        }
        return '';
    };
}

export const apiClient = {
    analytics: AnalyticsService,
    auth: AuthService,
    trading: TradingService,
    settings: SettingsService,
    approvals: ApprovalsService
};

export * from './api-client/generated';
