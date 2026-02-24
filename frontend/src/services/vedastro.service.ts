/**
 * VedAstro Service
 * 
 * Handles VedAstro signal generation and elemental consensus.
 */

import api from '@/lib/api';
import type { VedAstroSignal, ElementalConsensus, ElementalVotes } from '@/types';

/**
 * Get VedAstro signal for a symbol
 */
export async function getVedAstroSignal(
  symbol: string,
  price: number,
  date?: string
): Promise<VedAstroSignal> {
  const response = await api.get<VedAstroSignal>('/tools/vedastro', {
    params: { symbol, price, date },
  });
  return response.data;
}

/**
 * Get VedAstro signal (POST method)
 */
export async function getVedAstroSignalPost(
  symbol: string,
  currentPrice: number,
  date?: string
): Promise<VedAstroSignal> {
  const response = await api.post<VedAstroSignal>('/tools/vedastro', {
    symbol,
    current_price: currentPrice,
    date,
  });
  return response.data;
}

/**
 * Get elemental consensus for multiple symbols
 */
export async function getElementalConsensus(
  symbols: string[],
  weights?: Partial<ElementalVotes>
): Promise<ElementalConsensus[]> {
  const response = await api.post<{ results: ElementalConsensus[] }>('/tools/consensus', {
    symbols,
    fire_weight: weights?.fire || 0.3,
    earth_weight: weights?.earth || 0.3,
    water_weight: weights?.water || 0.2,
    air_weight: weights?.air || 0.2,
  });
  return response.data.results;
}

/**
 * Calculate position size
 */
export async function calculatePositionSize(
  symbol: string,
  portfolioValue: number,
  vedastroScore: number,
  priceHistory: number[]
): Promise<{
  symbol: string;
  position_size_eur: number;
  position_size_shares: number;
  confidence: number;
  constraints_applied: string[];
}> {
  const response = await api.post('/tools/position-size', {
    symbol,
    portfolio_value: portfolioValue,
    vedastro_score: vedastroScore,
    price_history: priceHistory,
  });
  return response.data;
}

/**
 * Calculate position size (GET method)
 */
export async function calculatePositionSizeGet(
  symbol: string,
  portfolioValue: number,
  vedastroScore: number,
  currentPrice: number
): Promise<{
  symbol: string;
  position_size_eur: number;
  position_size_shares: number;
  confidence: number;
  constraints_applied: string[];
}> {
  const response = await api.get('/tools/position-size', {
    params: {
      symbol,
      portfolio_value: portfolioValue,
      vedastro_score: vedastroScore,
      current_price: currentPrice,
    },
  });
  return response.data;
}

/**
 * Get health status
 */
export async function getHealthStatus(): Promise<{
  status: string;
  timestamp: string;
  components: Record<string, unknown>;
}> {
  const response = await api.get('/health');
  return response.data;
}

/**
 * Simple ping check
 */
export async function ping(): Promise<{ status: string; timestamp: string }> {
  const response = await api.get('/health/ping');
  return response.data;
}
