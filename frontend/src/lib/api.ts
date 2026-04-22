/**
 * API Client for Agentic Trader Platform
 *
 * All routes are mapped to the real backend (FastAPI).
 * Backend base: /api/v1/
 *   auth    → /api/v1/auth/...
 *   trading → /api/v1/trading/...
 *   kyc     → /api/v1/kyc/...
 *   agents  → /api/v1/agents/...
 *   navagraha → /api/v1/navagraha/...
 *   ooda    → /api/v1/ooda/...
 */

import axios from 'axios';
import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

import { API_URL as API_BASE_URL } from './config';

// Token storage (in-memory, not localStorage for security)
let accessToken: string | null = null;

/**
 * Set the access token for API requests.
 * Called by AuthContext when user authenticates.
 */
export function setApiToken(token: string | null) {
  accessToken = token;
}

/**
 * Get the current access token.
 */
export function getApiToken(): string | null {
  return accessToken;
}

/**
 * Unauthorized callback - registered by the auth context.
 * Called instead of hard-redirecting via window.location.href
 */
let _onUnauthorized: (() => void) | null = null;

export function setOnUnauthorized(cb: () => void): void {
  _onUnauthorized = cb;
}

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds for paper trading
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear token and trigger registered callback (no hard redirect)
      accessToken = null;
      if (_onUnauthorized) {
        _onUnauthorized();
      }
    }

    // Extract meaningful error message from backend
    const errorData = error.response?.data as { detail?: string; message?: string };
    if (errorData?.detail) {
      error.message = errorData.detail;
    } else if (errorData?.message) {
      error.message = errorData.message;
    }

    return Promise.reject(error);
  }
);

// ============================================================================
// AUTH API  →  /api/v1/auth/...
// ============================================================================

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    tenant_id: string;
    role: string;
    full_name: string | null;
  };
}

export const authApi = {
  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/register', data);
    return response.data;
  },

  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/login', data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    accessToken = null;
  },

  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// ============================================================================
// KYC API  →  /api/v1/kyc/...
// ============================================================================

export interface KYCData {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  nationality: string;
  phone_number: string;
  street_address: string;
  city: string;
  postal_code: string;
  country: string;
  id_type: 'passport' | 'drivers_license' | 'national_id';
  id_number: string;
  occupation: string;
  employment_status: string;
  annual_income: string;
  source_of_funds: string;
}

export interface KYCResponse {
  status: 'not_started' | 'in_progress' | 'pending_review' | 'verified' | 'rejected';
  submitted_at?: string;
  reviewed_at?: string;
  rejection_reason?: string;
  required: boolean;
  enabled: boolean;
}

export const kycApi = {
  getStatus: async (): Promise<KYCResponse> => {
    const response = await api.get<KYCResponse>('/kyc/status');
    return response.data;
  },

  submit: async (data: KYCData): Promise<{ success: boolean; message: string; status: string }> => {
    const response = await api.post('/kyc/submit', data);
    return response.data;
  },

  uploadDocuments: async (files: {
    id_front?: File;
    id_back?: File;
    selfie?: File;
  }): Promise<{ success: boolean; message: string; files_received: number }> => {
    const formData = new FormData();
    if (files.id_front) formData.append('id_front', files.id_front);
    if (files.id_back) formData.append('id_back', files.id_back);
    if (files.selfie) formData.append('selfie', files.selfie);
    const response = await api.post('/kyc/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  isRequired: async (): Promise<{ required: boolean; enabled: boolean; status: string }> => {
    const response = await api.get('/kyc/required');
    return response.data;
  },
};

// ============================================================================
// MARKETS API  →  /api/v1/trading/markets  +  /api/v1/trading/candles/{symbol}
// ============================================================================

export interface Asset {
  symbol: string;
  name: string;
  price: number;
  change24h: number;
  change24hValue: number;
  volume24h: number;
  marketCap?: number;
  sparkline?: number[];
  exchange?: string;
}

/** Market asset data for gainers/losers */
export interface MarketAsset {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
}

export interface TickerData {
  symbol: string;
  price: number;
  bid: number;
  ask: number;
  change: number;
  changePercent: number;
  volume: number;
  high24h: number;
  low24h: number;
}

/** Raw market data from backend */
interface RawMarketData {
  symbol?: string;
  id?: string;
  name?: string;
  base_currency?: string;
  base?: string;
  price?: number;
  last?: number;
  mark_price?: number;
  change?: number;
  change_24h?: number;
  price_change_percent?: number;
  change_value?: number;
  price_change?: number;
  volume?: number;
  volume_24h?: number;
  base_volume?: number;
  market_cap?: number;
  sparkline?: number[];
}

/** Normalize raw market entry from the backend into a frontend Asset */
function normalizeAsset(m: RawMarketData): Asset {
  return {
    symbol: m.symbol || m.id || '',
    name: m.name || m.base_currency || m.base || m.symbol || '',
    price: Number(m.price ?? m.last ?? m.mark_price ?? 0),
    change24h: Number(m.change ?? m.change_24h ?? m.price_change_percent ?? 0),
    change24hValue: Number(m.change_value ?? m.price_change ?? 0),
    volume24h: Number(m.volume ?? m.volume_24h ?? m.base_volume ?? 0),
    marketCap: m.market_cap ? Number(m.market_cap) : undefined,
    sparkline: Array.isArray(m.sparkline) ? m.sparkline : undefined,
  };
}

export const marketsApi = {
  /** GET /api/v1/trading/markets */
  getAssets: async (): Promise<Asset[]> => {
    const response = await api.get('/trading/markets');
    const raw = Array.isArray(response.data)
      ? response.data
      : Array.isArray(response.data?.markets)
        ? response.data.markets
        : [];
    return raw.map(normalizeAsset);
  },

  /** Derive ticker from the markets list */
  getTicker: async (symbol: string): Promise<TickerData | null> => {
    const response = await api.get('/trading/markets');
    const raw = Array.isArray(response.data)
      ? response.data
      : Array.isArray(response.data?.markets)
        ? response.data.markets
        : [];
    const m = raw.find(
      (r: RawMarketData) => (r.symbol || r.id || '').toLowerCase() === symbol.toLowerCase()
    );
    if (!m) return null;
    return {
      symbol: m.symbol || m.id,
      price: Number(m.price ?? m.last ?? 0),
      bid: Number(m.bid ?? m.price ?? 0),
      ask: Number(m.ask ?? m.price ?? 0),
      change: Number(m.change ?? 0),
      changePercent: Number(m.change_24h ?? m.change ?? 0),
      volume: Number(m.volume ?? m.volume_24h ?? 0),
      high24h: Number(m.high ?? m.high_24h ?? 0),
      low24h: Number(m.low ?? m.low_24h ?? 0),
    };
  },

  /** GET /api/v1/trading/candles/{symbol}?timeframe=1h&limit=100 */
  getOHLCV: async (symbol: string, timeframe: string = '1h', limit: number = 100) => {
    // Normalize symbol: BTC/EUR -> BTC-EUR (backend expects dash format)
    // Do NOT use encodeURIComponent — %2F causes Starlette to decode the slash
    // and split it into two path segments, breaking route matching → 404.
    const normalizedSymbol = symbol.replace(/\//g, '-');
    const response = await api.get(`/trading/candles/${normalizedSymbol}`, {
      params: { timeframe, limit },
    });
    // Backend may return { candles: [...] } or a plain array
    const raw = Array.isArray(response.data)
      ? response.data
      : Array.isArray(response.data?.candles)
        ? response.data.candles
        : [];
    interface RawCandle {
      time?: number;
      timestamp?: number;
      t?: number;
      open?: number;
      o?: number;
      high?: number;
      h?: number;
      low?: number;
      l?: number;
      close?: number;
      c?: number;
    }
    return raw.map((c: RawCandle) => ({
      time: c.time ?? c.timestamp ?? c.t ?? 0,
      open: Number(c.open ?? c.o ?? 0),
      high: Number(c.high ?? c.h ?? 0),
      low: Number(c.low ?? c.l ?? 0),
      close: Number(c.close ?? c.c ?? 0),
    }));
  },
};

// ============================================================================
// ORDERS API  →  /api/v1/trading/orders/...
// ============================================================================

export interface Order {
  id: string;
  symbol: string;
  type: 'market' | 'limit' | 'stop';
  side: 'buy' | 'sell';
  price: number;
  amount: number;
  filled: number;
  status: 'open' | 'filled' | 'cancelled' | 'partial';
  createdAt: string;
}

export interface CreateOrderRequest {
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit';
  amount: number;
  price?: number;
}

interface RawOrder {
  id?: string | number;
  order_id?: string | number;
  symbol?: string;
  instrument?: string;
  type?: string;
  order_type?: string;
  side?: string;
  direction?: string;
  price?: number;
  limit_price?: number;
  amount?: number;
  quantity?: number;
  size?: number;
  filled?: number;
  filled_quantity?: number;
  executed_quantity?: number;
  status?: string;
  state?: string;
  created_at?: string;
  createdAt?: string;
}

function normalizeOrder(o: RawOrder): Order {
  return {
    id: String(o.id ?? o.order_id ?? ''),
    symbol: o.symbol ?? o.instrument ?? '',
    type: (o.type ?? o.order_type ?? 'market').toLowerCase() as Order['type'],
    side: (o.side ?? o.direction ?? 'buy').toLowerCase() as Order['side'],
    price: Number(o.price ?? o.limit_price ?? 0),
    amount: Number(o.amount ?? o.quantity ?? o.size ?? 0),
    filled: Number(o.filled ?? o.filled_quantity ?? o.executed_quantity ?? 0),
    status: normalizeOrderStatus(o.status ?? o.state ?? 'open'),
    createdAt: o.created_at ?? o.createdAt ?? new Date().toISOString(),
  };
}

function normalizeOrderStatus(raw: string): Order['status'] {
  const s = raw.toLowerCase();
  if (s === 'filled' || s === 'complete' || s === 'completed') return 'filled';
  if (s === 'cancelled' || s === 'canceled') return 'cancelled';
  if (s === 'partial' || s === 'partially_filled') return 'partial';
  return 'open';
}

export const ordersApi = {
  /** GET /api/v1/trading/orders/active */
  getOrders: async (): Promise<Order[]> => {
    const response = await api.get('/trading/orders/active');
    const raw = Array.isArray(response.data)
      ? response.data
      : Array.isArray(response.data?.orders)
        ? response.data.orders
        : [];
    return raw.map(normalizeOrder);
  },

  /** POST /api/v1/trading/orders */
  createOrder: async (data: CreateOrderRequest): Promise<Order> => {
    const response = await api.post('/trading/orders', data);
    return normalizeOrder(response.data?.order ?? response.data);
  },

  /** DELETE /api/v1/trading/orders/{orderId} – cancel a single order */
  cancelOrder: async (orderId: string): Promise<void> => {
    await api.delete(`/trading/orders/${orderId}`);
  },

  /** GET /api/v1/trading/orders/history */
  getOrderHistory: async (limit = 50): Promise<Order[]> => {
    const response = await api.get('/trading/orders/history', { params: { limit } });
    const raw = Array.isArray(response.data)
      ? response.data
      : Array.isArray(response.data?.orders)
        ? response.data.orders
        : [];
    return raw.map(normalizeOrder);
  },
};

// ============================================================================
// PORTFOLIO API  →  /api/v1/trading/portfolio  +  /api/v1/trading/history
// ============================================================================

export interface Holding {
  symbol: string;
  name: string;
  amount: number;
  avgPrice: number;
  currentPrice: number;
  value: number;
  pnl: number;
  pnlPercent: number;
}

export interface TradeHistory {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  price: number;
  amount: number;
  total: number;
  timestamp: string;
  type?: string;
}

export interface PortfolioPerformance {
  totalValue: number;
  totalPnl: number;
  totalPnlPercent: number;
  dailyPnl: number;
  weeklyPnl: number;
  monthlyPnl: number;
  availableBalance: number;
}

interface RawHolding {
  amount?: number;
  quantity?: number;
  balance?: number;
  avg_price?: number;
  average_price?: number;
  avg_cost?: number;
  current_price?: number;
  price?: number;
  mark_price?: number;
  value?: number;
  market_value?: number;
  pnl?: number;
  unrealized_pnl?: number;
  profit_loss?: number;
  pnl_percent?: number;
  pnl_percentage?: number;
  symbol?: string;
  instrument?: string;
  name?: string;
  asset_name?: string;
}

function normalizeHolding(h: RawHolding): Holding {
  const amount = Number(h.amount ?? h.quantity ?? h.balance ?? 0);
  const avgPrice = Number(h.avg_price ?? h.average_price ?? h.avg_cost ?? 0);
  const currentPrice = Number(h.current_price ?? h.price ?? h.mark_price ?? 0);
  const value = Number(h.value ?? h.market_value ?? amount * currentPrice);
  const pnl = Number(h.pnl ?? h.unrealized_pnl ?? h.profit_loss ?? 0);
  const pnlPercent = Number(h.pnl_percent ?? h.pnl_percentage ?? (avgPrice ? (pnl / (amount * avgPrice)) * 100 : 0));
  return {
    symbol: h.symbol ?? h.instrument ?? '',
    name: h.name ?? h.asset_name ?? h.symbol ?? '',
    amount,
    avgPrice,
    currentPrice,
    value,
    pnl,
    pnlPercent,
  };
}

interface RawTradeHistory {
  id?: string | number;
  trade_id?: string | number;
  amount?: number;
  quantity?: number;
  size?: number;
  price?: number;
  executed_price?: number;
  symbol?: string;
  instrument?: string;
  side?: string;
  direction?: string;
  total?: number;
  notional?: number;
  timestamp?: string;
  executed_at?: string;
  created_at?: string;
  type?: string;
  order_type?: string;
}

function normalizeTradeHistory(t: RawTradeHistory): TradeHistory {
  const amount = Number(t.amount ?? t.quantity ?? t.size ?? 0);
  const price = Number(t.price ?? t.executed_price ?? 0);
  return {
    id: String(t.id ?? t.trade_id ?? Math.random()),
    symbol: t.symbol ?? t.instrument ?? '',
    side: (t.side ?? t.direction ?? 'buy').toLowerCase() as 'buy' | 'sell',
    price,
    amount,
    total: Number(t.total ?? t.notional ?? price * amount),
    timestamp: t.timestamp ?? t.executed_at ?? t.created_at ?? new Date().toISOString(),
    type: t.type ?? t.order_type ?? 'market',
  };
}

export const portfolioApi = {
  /** GET /api/v1/trading/portfolio */
  getHoldings: async (): Promise<Holding[]> => {
    const response = await api.get('/trading/portfolio');
    const raw = Array.isArray(response.data)
      ? response.data
      : Array.isArray(response.data?.holdings)
        ? response.data.holdings
        : Array.isArray(response.data?.positions)
          ? response.data.positions
          : [];
    return raw.map(normalizeHolding);
  },

  /** GET /api/v1/trading/history */
  getHistory: async (): Promise<TradeHistory[]> => {
    const response = await api.get('/trading/history');
    const raw = Array.isArray(response.data)
      ? response.data
      : Array.isArray(response.data?.trades)
        ? response.data.trades
        : Array.isArray(response.data?.history)
          ? response.data.history
          : [];
    return raw.map(normalizeTradeHistory);
  },

  /** GET /api/v1/trading/portfolio – extract performance metrics from same endpoint */
  getPerformance: async (): Promise<PortfolioPerformance> => {
    const response = await api.get('/trading/portfolio');
    const d = response.data;
    return {
      totalValue: Number(d?.total_value ?? d?.totalValue ?? d?.portfolio_value ?? 0),
      totalPnl: Number(d?.total_pnl ?? d?.totalPnl ?? d?.unrealized_pnl ?? 0),
      totalPnlPercent: Number(d?.total_pnl_percent ?? d?.totalPnlPercent ?? d?.pnl_percent ?? 0),
      dailyPnl: Number(d?.daily_pnl ?? d?.dailyPnl ?? 0),
      weeklyPnl: Number(d?.weekly_pnl ?? d?.weeklyPnl ?? 0),
      monthlyPnl: Number(d?.monthly_pnl ?? d?.monthlyPnl ?? 0),
      availableBalance: Number(
        d?.available_balance ?? d?.cash_balance ?? d?.balance ?? d?.free_cash ?? 0
      ),
    };
  },
};

// ============================================================================
// AGENTS API  →  /api/v1/agents/...
// ============================================================================

export interface AgentStrategy {
  id: string;
  name: string;
  type: string;
  status: 'running' | 'paused' | 'error';
  performance: number;
  trades: number;
  prana?: number;
}

export interface AgentInfo {
  id?: string;
  name?: string;
  type?: string;
  status?: string;
  strategy?: string;
  performance?: number;
  trades?: number;
  prana?: number;
  is_active?: boolean;
  state?: {
    total_trades?: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

/** Agent trade data */
export interface AgentTrade {
  id: string;
  agent_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  amount: number;
  price: number;
  timestamp: string;
  status: 'open' | 'closed' | 'cancelled';
  pnl?: number;
}

export interface AgentsStatusResponse {
  agents: Record<string, AgentInfo>;
  count: number;
  orchestrator_state?: {
    guna_balance?: Record<string, number>;
    global_coherence?: number;
  };
}

export const agentsApi = {
  /** GET /api/v1/agents/status */
  getStatus: async (): Promise<AgentsStatusResponse> => {
    const response = await api.get<AgentsStatusResponse>('/agents/status');
    return response.data;
  },

  /** POST /api/v1/agents/chat - Get advice from AI advisor */
  chat: async (message: string, history: ChatHistoryEntry[] = []): Promise<{ response: string }> => {
    const response = await api.post<{ response: string }>('/agents/chat', { message, history });
    return response.data;
  },

  /** POST /api/v1/agents/run-cycle - Trigger agent analysis */
  runCycle: async (): Promise<{ 
    insights: string; 
    market_data: { gainers: MarketAsset[]; losers: MarketAsset[] }; 
    agents_triggered: number; 
    trades_generated?: number 
  }> => {
    const response = await api.post('/agents/run-cycle', {});
    return response.data;
  },

  /** GET /api/v1/agents/trades - Get agent trade history */
  getTrades: async (): Promise<{ trades: AgentTrade[]; count: number }> => {
    const response = await api.get('/agents/trades');
    return response.data;
  },
};

// ============================================================================
// CHAT API  →  /api/v1/agents/chat
// ============================================================================

export interface ChatHistoryEntry {
  type: 'user' | 'ai' | 'system';
  content: string;
}

export const chatApi = {
  /** POST /api/v1/agents/chat */
  sendMessage: async (message: string, history: ChatHistoryEntry[] = []): Promise<string> => {
    const response = await api.post<{ response: string }>('/agents/chat', { message, history });
    return response.data.response;
  },
};

// ============================================================================
// NAVAGRAHA API  →  /api/v1/navagraha/current-state
// ============================================================================

export interface NavagrahaState {
  current_dasha: string;
  guna_distribution: {
    sattva: number;
    rajas: number;
    tamas: number;
  };
  trading_gate_open: boolean;
  consciousness_level: number;
}

export const navagrahaApi = {
  getCurrentState: async (): Promise<NavagrahaState> => {
    const response = await api.get<NavagrahaState>('/navagraha/current-state');
    return response.data;
  },
};

// ============================================================================
// OODA API  →  /api/v1/ooda/current-cycle
// ============================================================================

export interface OODAState {
  phase: 'observe' | 'orient' | 'decide' | 'act';
  cycle_id: string;
  coherence: number;
  confidence: number;
  timestamp: string;
}

export const oodaApi = {
  getCurrentCycle: async (): Promise<OODAState> => {
    const response = await api.get<OODAState>('/ooda/current-cycle');
    return response.data;
  },
};

// ============================================================================
// FEDERATED TRIAD API  →  /api/v1/federated/...
// ============================================================================

export interface CouncilView {
  name: string;
  type: 'guna' | 'elemental' | 'graha' | 'mind' | 'body';
  perspective: string;
  confidence: number;
  insights: string[];
  contradictions?: string[];
  status?: 'active' | 'idle' | 'error';
}

export interface ChittaNode {
  id: string;
  content: string;
  source: string;
  timestamp: string;
  council: string;
  verified: boolean;
}

export interface BuddhiDecision {
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  rationale: string;
  supporting: string[];
  opposing: string[];
  contradictions: number;
  timestamp: string;
}

export interface FederatedState {
  coherence: {
    total: number;
    harmony: number;
    performance: number;
    chitta_health: number;
    deliberation_quality: number;
    buddhi_clarity: number;
  };
  councils: CouncilView[];
  chitta: {
    nodes: ChittaNode[];
    total_nodes: number;
    verified_nodes: number;
  };
  latest_decision: BuddhiDecision | null;
  deliberation_steps: {
    iteration: number;
    council: string;
    perspective: string;
    confidence: number;
  }[];
}

export const federatedApi = {
  /** GET /api/v1/federated/state - Get complete Federated Triad state */
  getState: async (): Promise<FederatedState> => {
    const response = await api.get<FederatedState>('/federated/state');
    return response.data;
  },

  /** GET /api/v1/federated/agents - Get list of federated agents */
  getAgents: async (): Promise<{ agents: Array<{
    id: string;
    name: string;
    status: string;
    type: string;
    trades: number;
    pnl: number;
    confidence: number;
  }> }> => {
    const response = await api.get('/federated/agents');
    return response.data;
  },

  /** POST /api/v1/federated/sync - Trigger federated sync */
  triggerSync: async (): Promise<{ status: string; round_id: string; agents_synced: number }> => {
    const response = await api.post('/federated/sync', {});
    return response.data;
  },

  /** POST /api/v1/federated/cycle - Trigger a full Federated Triad cycle */
  runCycle: async (): Promise<{
    decision: BuddhiDecision;
    coherence: FederatedState['coherence'];
    insights: string;
  }> => {
    const response = await api.post('/federated/cycle', {});
    return response.data;
  },
};

// ============================================================================
// SETTINGS API  →  /api/v1/settings/...
// ============================================================================

export interface UserProfile {
  first_name: string;
  last_name: string;
  email: string | null;
}

export interface NotificationSettings {
  order_executions: boolean;
  price_alerts: boolean;
  ai_signals: boolean;
  security_alerts: boolean;
}

export interface SecuritySettings {
  two_factor_enabled: boolean;
  last_password_change: string | null;
}

export interface AppearanceSettings {
  theme: 'dark' | 'light' | 'system';
}

export interface UserPreferences {
  default_currency: 'EUR' | 'USD' | 'GBP';
  default_exchange: 'binance' | 'kraken' | 'coinbase' | 'bitvavo';
}

export interface AllSettings {
  profile: UserProfile;
  notifications: NotificationSettings;
  security: SecuritySettings;
  appearance: AppearanceSettings;
  preferences: UserPreferences;
  api_keys: Array<{
    id: string;
    exchange: string;
    api_key_masked: string;
    created_at: string;
    is_valid: boolean;
  }>;
}

export const settingsApi = {
  /** GET /api/v1/settings/all - Get all settings at once */
  getAll: async (): Promise<AllSettings> => {
    const response = await api.get<AllSettings>('/settings/all');
    return response.data;
  },

  /** GET /api/v1/settings/profile */
  getProfile: async (): Promise<UserProfile> => {
    const response = await api.get<UserProfile>('/settings/profile');
    return response.data;
  },

  /** PUT /api/v1/settings/profile */
  updateProfile: async (profile: UserProfile): Promise<UserProfile> => {
    const response = await api.put<UserProfile>('/settings/profile', profile);
    return response.data;
  },

  /** GET /api/v1/settings/notifications */
  getNotifications: async (): Promise<NotificationSettings> => {
    const response = await api.get<NotificationSettings>('/settings/notifications');
    return response.data;
  },

  /** PUT /api/v1/settings/notifications */
  updateNotifications: async (settings: NotificationSettings): Promise<NotificationSettings> => {
    const response = await api.put<NotificationSettings>('/settings/notifications', settings);
    return response.data;
  },

  /** GET /api/v1/settings/security */
  getSecurity: async (): Promise<SecuritySettings> => {
    const response = await api.get<SecuritySettings>('/settings/security');
    return response.data;
  },

  /** POST /api/v1/settings/security/2fa */
  toggle2FA: async (enabled: boolean): Promise<{ enabled: boolean }> => {
    const response = await api.post<{ enabled: boolean }>('/settings/security/2fa', null, {
      params: { enabled },
    });
    return response.data;
  },

  /** POST /api/v1/settings/security/password */
  changePassword: async (currentPassword: string, newPassword: string): Promise<{ success: boolean }> => {
    const response = await api.post<{ success: boolean }>('/settings/security/password', null, {
      params: { current_password: currentPassword, new_password: newPassword },
    });
    return response.data;
  },

  /** GET /api/v1/settings/appearance */
  getAppearance: async (): Promise<AppearanceSettings> => {
    const response = await api.get<AppearanceSettings>('/settings/appearance');
    return response.data;
  },

  /** PUT /api/v1/settings/appearance */
  updateAppearance: async (settings: AppearanceSettings): Promise<AppearanceSettings> => {
    const response = await api.put<AppearanceSettings>('/settings/appearance', settings);
    return response.data;
  },

  /** GET /api/v1/settings/preferences */
  getPreferences: async (): Promise<UserPreferences> => {
    const response = await api.get<UserPreferences>('/settings/preferences');
    return response.data;
  },

  /** PUT /api/v1/settings/preferences */
  updatePreferences: async (prefs: UserPreferences): Promise<UserPreferences> => {
    const response = await api.put<UserPreferences>('/settings/preferences', prefs);
    return response.data;
  },

  /** GET /api/v1/settings/api-keys */
  getApiKeys: async () => {
    const response = await api.get('/settings/api-keys');
    return response.data;
  },

  /** POST /api/v1/settings/api-keys */
  addApiKey: async (data: { exchange: string; api_key: string; api_secret: string; passphrase?: string }) => {
    const response = await api.post('/settings/api-keys', data);
    return response.data;
  },

  /** DELETE /api/v1/settings/api-keys/{keyId} */
  deleteApiKey: async (keyId: string) => {
    const response = await api.delete(`/settings/api-keys/${keyId}`);
    return response.data;
  },
};

// ============================================================================
// COMPETITIONS API  →  /api/v1/competitions/...
// ============================================================================

export interface Tournament {
  id: string;
  name: string;
  description: string;
  type: string;
  participants: number;
  max_participants: number;
  ends_at: string;
  time_remaining: string;
  entry_fee: number;
  prize_pool: number;
}

export interface LeagueInfo {
  tier: string;
  name: string;
  min_points: number;
  max_points: number;
  current_members: number;
  max_members: number;
}

export interface LeaderboardEntry {
  rank: number;
  competitor_id: string;
  name: string;
  tier: string;
  points: number;
  win_rate: number;
  total_pnl: number;
}

export const competitionsApi = {
  /** GET /api/v1/competitions/tournaments?status=active|upcoming */
  getTournaments: async (status: 'active' | 'upcoming' = 'active'): Promise<{ tournaments: Tournament[]; count: number }> => {
    const response = await api.get('/competitions/tournaments', { params: { status } });
    return response.data;
  },

  /** GET /api/v1/competitions/league-info */
  getLeagueInfo: async (): Promise<Record<string, LeagueInfo>> => {
    const response = await api.get('/competitions/league-info');
    return response.data;
  },

  /** POST /api/v1/competitions/enter */
  enterTournament: async (competitorId: string, tournamentId: string): Promise<{ success: boolean; error?: string }> => {
    const response = await api.post('/competitions/enter', { competitor_id: competitorId, tournament_id: tournamentId });
    return response.data;
  },

  /** GET /api/v1/competitions/leaderboard */
  getLeaderboard: async (tier?: string, limit: number = 20): Promise<{ entries: LeaderboardEntry[]; total: number }> => {
    const response = await api.get('/competitions/leaderboard', { params: { tier, limit } });
    return response.data;
  },

  /** GET /api/v1/competitions/badges/{competitorId} */
  getBadges: async (competitorId: string): Promise<{ competitor_id: string; badges: string[]; total_badges: number }> => {
    const response = await api.get(`/competitions/badges/${competitorId}`);
    return response.data;
  },
};

// ============================================================================
// ERROR HANDLING
// ============================================================================

export interface ApiError {
  message: string;
  code: string;
  status: number;
}

interface ErrorResponseData {
  detail?: string;
  message?: string;
  code?: string;
}

export const handleApiError = (error: AxiosError): ApiError => {
  if (error.response) {
    const data = error.response.data as ErrorResponseData;
    return {
      message: data.detail || data.message || 'An error occurred',
      code: data.code || 'UNKNOWN_ERROR',
      status: error.response.status,
    };
  } else if (error.request) {
    return {
      message: 'No response from server. Please check your connection.',
      code: 'NETWORK_ERROR',
      status: 0,
    };
  }
  return {
    message: error.message || 'An unexpected error occurred',
    code: 'UNKNOWN_ERROR',
    status: 0,
  };
};

// ============================================================================
// WEBSOCKET CLIENT (Stub - use WebSocketContext instead)
// ============================================================================

export const wsClient = {
  connect: () => { console.warn('wsClient deprecated, use WebSocketContext'); },
  disconnect: () => {
    // Deprecated - use WebSocketContext instead
  },
  subscribe: (channel: string) => { 
    console.warn('Subscribe to', channel, '- use WebSocketContext'); 
  },
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  unsubscribe: (_channel: string) => {
    // Deprecated - use WebSocketContext instead
  },
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  addListener: (_callback: (msg: unknown) => void) => {
    console.warn('wsClient deprecated, use WebSocketContext');
    return () => {
      // Cleanup function
    };
  },
};

export default api;
