/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TradingService {
    /**
     * Get Markets
     * Get available markets data.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getMarketsApiV1TradingMarketsGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/trading/markets',
        });
    }
    /**
     * Get Candles
     * Get OHLCV candles for a symbol.
     * @param symbol
     * @param timeframe
     * @param limit
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getCandlesApiV1TradingCandlesSymbolGet(
        symbol: string,
        timeframe: string = '1m',
        limit: number = 100,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/trading/candles/{symbol}',
            path: {
                'symbol': symbol,
            },
            query: {
                'timeframe': timeframe,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Portfolio
     * Get portfolio holdings and stats.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPortfolioApiV1TradingPortfolioGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/trading/portfolio',
        });
    }
    /**
     * Get History
     * Get trade history.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getHistoryApiV1TradingHistoryGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/trading/history',
        });
    }
    /**
     * Create Order
     * Create and execute a new order.
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createOrderApiV1TradingOrdersPost(
        requestBody: Record<string, any>,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/trading/orders',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Cancel All Orders
     * Emergency: Cancel all open orders for the tenant.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static cancelAllOrdersApiV1TradingOrdersDelete(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/trading/orders',
        });
    }
    /**
     * Get Active Orders
     * Get all active orders (OPEN, PENDING, PARTIALLY_FILLED).
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getActiveOrdersApiV1TradingOrdersActiveGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/trading/orders/active',
        });
    }
    /**
     * Get Order History
     * Get historical orders (FILLED, CANCELLED, etc).
     * @param limit
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getOrderHistoryApiV1TradingOrdersHistoryGet(
        limit: number = 50,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/trading/orders/history',
            query: {
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
