/**
 * Paper Trading API Client
 * 
 * All endpoints for paper trading functionality.
 * NO MOCK DATA - 100% real backend integration.
 */

import api from '../../api';

// ============================================================================
// TYPES
// ============================================================================

export interface Trade {
  id: string;
  timestamp: string;
  symbol: string;
  side: 'buy' | 'sell';
  qty: number;
  price: number;
  value: number;
  agent: string;
  exchange: string;
  pnl?: number;
}

export interface Position {
  symbol: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
}

export interface Portfolio {
  cash: number;
  positions: Record<string, Position>;
  total_value: number;
  pnl: number;
  pnl_percent: number;
  buying_power: number;
}

export interface SessionStats {
  total_trades: number;
  buy_trades: number;
  sell_trades: number;
  avg_trade_value: number;
  avg_profit_loss: number;
  win_rate: number;
  uptime_seconds: number;
}

export interface PaperTradingSession {
  id: string;
  is_running: boolean;
  started_at: string;
  config: {
    duration: number;
    capital: number;
  };
  portfolio: Portfolio;
  stats: SessionStats;
  trades: Trade[];
}

export interface StartSessionRequest {
  duration: number;  // hours
  capital: number;   // initial capital
  symbols?: string[]; // allowed symbols (optional)
  strategy?: string;  // strategy configuration (optional)
}

export interface StartSessionResponse {
  status: 'started';
  session_id: string;
  started_at: string;
}

export interface StopSessionResponse {
  status: 'stopped';
  session_id: string;
  stopped_at: string;
  final_portfolio: Portfolio;
  total_return: number;
  total_return_percent: number;
}

export interface SessionStatusResponse {
  is_running: boolean;
  session_id?: string;
  portfolio?: Portfolio;
  stats?: SessionStats;
  trades?: Trade[];
  uptime_seconds?: number;
}

export interface AgentDecision {
  timestamp: string;
  agent: string;
  strategy: string;
  symbol: string;
  decision: 'buy' | 'sell' | 'hold';
  confidence: number;
  reason: string;
  executed: boolean;
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

/**
 * Start a new paper trading session
 */
export async function startSession(data: StartSessionRequest): Promise<StartSessionResponse> {
  const response = await api.post<StartSessionResponse>('/paper-trading/start', data);
  return response.data;
}

/**
 * Stop the current paper trading session
 */
export async function stopSession(): Promise<StopSessionResponse> {
  const response = await api.post<StopSessionResponse>('/paper-trading/stop');
  return response.data;
}

/**
 * Get current session status
 */
export async function getSessionStatus(): Promise<SessionStatusResponse> {
  const response = await api.get<SessionStatusResponse>('/paper-trading/status');
  return response.data;
}

/**
 * Get session statistics
 */
export async function getSessionStats(): Promise<SessionStats> {
  const response = await api.get<SessionStats>('/paper-trading/stats');
  return response.data;
}

/**
 * Get portfolio details
 */
export async function getPortfolio(): Promise<Portfolio> {
  const response = await api.get<Portfolio>('/paper-trading/portfolio');
  return response.data;
}

/**
 * Get trade history
 */
export async function getTradeHistory(limit = 50): Promise<Trade[]> {
  const response = await api.get<Trade[]>('/paper-trading/trades', {
    params: { limit }
  });
  return response.data;
}

/**
 * Get agent decisions
 */
export async function getAgentDecisions(): Promise<AgentDecision[]> {
  const response = await api.get<AgentDecision[]>('/paper-trading/decisions');
  return response.data;
}

// ============================================================================
// WEBSOCKET
// ============================================================================

export const PAPER_TRADING_WS_PATH = '/ws/paper-trading';

export type WebSocketMessage =
  | { type: 'trade'; data: Trade }
  | { type: 'portfolio'; data: Portfolio }
  | { type: 'stats'; data: SessionStats }
  | { type: 'decision'; data: AgentDecision }
  | { type: 'connected'; session_id: string }
  | { type: 'error'; message: string };

// ============================================================================
// EXPORTS
// ============================================================================

export const paperTradingApi = {
  startSession,
  stopSession,
  getSessionStatus,
  getSessionStats,
  getPortfolio,
  getTradeHistory,
  getAgentDecisions,
};

export default paperTradingApi;
