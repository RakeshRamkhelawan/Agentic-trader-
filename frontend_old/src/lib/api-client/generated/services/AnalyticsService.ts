/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnalyticsMetrics } from '../models/AnalyticsMetrics';
import type { PerformanceResponse } from '../models/PerformanceResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AnalyticsService {
    /**
     * Get Performance Metrics
     * Calculate performance metrics based on trade history.
     * @returns PerformanceResponse Successful Response
     * @throws ApiError
     */
    public static getPerformanceMetricsApiV1AnalyticsPerformanceGet(): CancelablePromise<PerformanceResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/performance',
        });
    }
    /**
     * Get Dashboard Metrics
     * Get aggregated dashboard metrics including Mahabhutas Coherence.
     * @returns AnalyticsMetrics Successful Response
     * @throws ApiError
     */
    public static getDashboardMetricsApiV1AnalyticsMetricsGet(): CancelablePromise<AnalyticsMetrics> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/metrics',
        });
    }
}
