/**
 * Backtest Service
 * 
 * Handles all backtesting-related API calls.
 */

import { api } from '@/lib/api';
import type { BacktestConfig, BacktestResult } from '@/types';

/**
 * Run a new backtest
 */
export async function runBacktest(config: BacktestConfig): Promise<{
  backtestId: string;
  status: string;
}> {
  const response = await api.post('/backtest/run', config);
  return response.data;
}

/**
 * Get backtest result by ID
 */
export async function getBacktestResult(backtestId: string): Promise<BacktestResult> {
  const response = await api.get<BacktestResult>(`/backtest/${backtestId}`);
  return response.data;
}

/**
 * Get all backtests for user
 */
export async function getBacktests(
  limit?: number,
  offset?: number
): Promise<BacktestResult[]> {
  const response = await api.get<BacktestResult[]>('/backtest/list', {
    params: { limit, offset },
  });
  return response.data;
}

/**
 * Run batch backtests
 */
export async function runBatchBacktest(
  configs: BacktestConfig[]
): Promise<{
  batchId: string;
  total: number;
  successful: number;
  failed: number;
}> {
  const response = await api.post('/backtest/batch', { configs });
  return response.data;
}

/**
 * Get cache statistics
 */
export async function getCacheStats(): Promise<{
  hits: number;
  misses: number;
  hitRate: number;
  size: number;
}> {
  const response = await api.get('/backtest/cache/stats');
  return response.data;
}

/**
 * Clear cache
 */
export async function clearCache(): Promise<void> {
  await api.post('/backtest/cache/clear');
}

/**
 * Stream backtest progress (for WebSocket implementation)
 */
export function createBacktestProgressStream(
  backtestId: string,
  onProgress: (progress: number) => void
): () => void {
  // This would connect to WebSocket in a real implementation
  // For now, we'll poll
  const interval = setInterval(async () => {
    try {
      const result = await getBacktestResult(backtestId);
      if (result.status === 'completed') {
        onProgress(100);
        clearInterval(interval);
      } else if (result.status === 'running') {
        // Estimate progress based on trades vs expected
        onProgress(50); // Placeholder
      }
    } catch (error) {
      clearInterval(interval);
    }
  }, 1000);

  // Return cleanup function
  return () => clearInterval(interval);
}
