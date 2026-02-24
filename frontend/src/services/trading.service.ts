/**
 * Trading Service
 * 
 * Handles all trading-related API calls.
 * Portfolio, positions, orders, and market data.
 */

import axios from 'axios';
import api from '@/lib/api';
import type { Portfolio, Position, Trade } from '@/types';

/**
 * Get user portfolio
 */
export async function getPortfolio(): Promise<Portfolio> {
  const response = await api.get<Portfolio>('/trading/portfolio');
  return response.data;
}

/**
 * Get all positions
 */
export async function getPositions(): Promise<Position[]> {
  const response = await api.get<Position[]>('/trading/positions');
  return response.data;
}

/**
 * Get position for specific symbol
 */
export async function getPosition(symbol: string): Promise<Position | null> {
  try {
    const response = await api.get<Position>(`/trading/positions/${symbol}`);
    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null;
    }
    throw error;
  }
}

/**
 * Execute trade
 */
export async function executeTrade(
  symbol: string,
  action: 'buy' | 'sell',
  quantity: number,
  orderType?: 'market' | 'limit',
  limitPrice?: number
): Promise<Trade> {
  const response = await api.post<Trade>('/trading/execute', {
    symbol,
    action,
    quantity,
    order_type: orderType || 'market',
    limit_price: limitPrice,
  });
  return response.data;
}

/**
 * Get trade history
 */
export async function getTradeHistory(
  limit?: number,
  offset?: number
): Promise<Trade[]> {
  const response = await api.get<Trade[]>('/trading/history', {
    params: { limit, offset },
  });
  return response.data;
}

/**
 * Get market data for symbol
 */
export async function getMarketData(symbol: string): Promise<{
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  previousClose: number;
  timestamp: string;
}> {
  const response = await api.get(`/trading/market-data/${symbol}`);
  return response.data;
}

/**
 * Search symbols
 */
export async function searchSymbols(query: string): Promise<Array<{
  symbol: string;
  name: string;
  type: string;
  exchange: string;
}>> {
  const response = await api.get('/trading/search', {
    params: { q: query },
  });
  return response.data;
}

/**
 * Get market regime
 */
export async function getMarketRegime(): Promise<{
  regime: 'bullish' | 'bearish' | 'neutral' | 'volatile';
  confidence: number;
  indicators: Record<string, number>;
}> {
  const response = await api.get('/trading/market-regime');
  return response.data;
}
