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
import type { AxiosError, AxiosInstance } from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
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
      localStorage.removeItem('access_token');
      window.location.href = '/login';
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
    localStorage.removeItem('access_token');
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

/** Normalize raw market entry from the backend into a frontend Asset */
function normalizeAsset(m: any): Asset {
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
      (r: any) => (r.symbol || r.id || '').toLowerCase() === symbol.toLowerCase()
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
    return raw.map((c: any) => ({
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

function normalizeOrder(o: any): Order {
  return {
    id: String(o.id ?? o.order_id ?? ''),
    symbol: o.symbol ?? o.instrument ?? '',
    type: (o.type ?? o.order_type ?? 'market').toLowerCase(),
    side: (o.side ?? o.direction ?? 'buy').toLowerCase(),
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

function normalizeHolding(h: any): Holding {
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

function normalizeTradeHistory(t: any): TradeHistory {
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

export interface AgentsStatusResponse {
  agents: Record<string, any>;
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
  runCycle: async (): Promise<{ insights: string; market_data: { gainers: any[]; losers: any[] }; agents_triggered: number; trades_generated?: number }> => {
    const response = await api.post('/agents/run-cycle', {});
    return response.data;
  },
  
  /** GET /api/v1/agents/trades - Get agent trade history */
  getTrades: async (): Promise<{ trades: any[]; count: number }> => {
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
    try {
      const response = await api.get<FederatedState>('/federated/state');
      return response.data;
    } catch (error) {
      // Return mock data if endpoint doesn't exist yet
      console.warn('Federated API not available, using mock data');
      return {
        coherence: {
          total: 75,
          harmony: 80,
          performance: 100,
          chitta_health: 85,
          deliberation_quality: 70,
          buddhi_clarity: 75
        },
        councils: [],
        chitta: { nodes: [], total_nodes: 0, verified_nodes: 0 },
        latest_decision: null,
        deliberation_steps: []
      };
    }
  },
  
  /** POST /api/v1/federated/cycle - Trigger a full Federated Triad cycle */
  runCycle: async (): Promise<{ 
    decision: BuddhiDecision; 
    coherence: FederatedState['coherence'];
    insights: string;
  }> => {
    try {
      const response = await api.post('/federated/cycle', {});
      return response.data;
    } catch (error) {
      console.warn('Federated cycle API not available, falling back to agents API');
      // Fallback to regular agents API
      const result = await agentsApi.runCycle();
      return {
        decision: {
          action: 'hold',
          confidence: 0.5,
          rationale: result.insights,
          supporting: [],
          opposing: [],
          contradictions: 0,
          timestamp: new Date().toISOString()
        },
        coherence: {
          total: 75,
          harmony: 80,
          performance: 100,
          chitta_health: 85,
          deliberation_quality: 70,
          buddhi_clarity: 75
        },
        insights: result.insights
      };
    }
  },
};

// ============================================================================
// WEBSOCKET CLIENT
// Backend protocol:
//   subscribe:   { type: "subscribe",   channel: "ticker.BTC-EUR" }
//   unsubscribe: { type: "unsubscribe", channel: "ticker.BTC-EUR" }
//   ping:        { type: "ping" }
// ============================================================================

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private pendingChannels: Set<string> = new Set();
  private listeners: Set<(data: any) => void> = new Set();
  private onConnectCb?: () => void;
  private onDisconnectCb?: () => void;

  constructor(private url: string) {}

  /**
   * Add a message listener. Returns a cleanup function to remove it.
   * Multiple components can each call addListener without stepping on each other.
   */
  addListener(fn: (data: any) => void): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  /**
   * Connect (idempotent).
   * If a socket is already OPEN or CONNECTING this is a no-op.
   */
  connect(onConnect?: () => void, onDisconnect?: () => void) {
    if (onConnect) this.onConnectCb = onConnect;
    if (onDisconnect) this.onDisconnectCb = onDisconnect;

    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN ||
        this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    this._openSocket();
  }

  private _openSocket() {
    const token = localStorage.getItem('access_token');
    const wsUrl = token ? `${this.url}?token=${token}` : this.url;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.onConnectCb?.();
      // Re-subscribe to all tracked channels after (re)connect
      this.pendingChannels.forEach((ch) => this._send({ type: 'subscribe', channel: ch }));
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.listeners.forEach((fn) => fn(data));
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.onDisconnectCb?.();
      this._attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private _attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
      setTimeout(() => this._openSocket(), this.reconnectDelay * this.reconnectAttempts);
    }
  }

  private _send(msg: object) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  disconnect() {
    this.pendingChannels.clear();
    this.ws?.close();
    this.ws = null;
  }

  /** Subscribe to a channel – backend expects { type: "subscribe", channel: "..." } */
  subscribe(channel: string) {
    this.pendingChannels.add(channel);
    this._send({ type: 'subscribe', channel });
  }

  /** Unsubscribe from a channel */
  unsubscribe(channel: string) {
    this.pendingChannels.delete(channel);
    this._send({ type: 'unsubscribe', channel });
  }
}

export const wsClient = new WebSocketClient(
  API_BASE_URL.replace(/^http/, 'ws') + '/ws'
);

// ============================================================================
// ERROR HANDLING
// ============================================================================

export interface ApiError {
  message: string;
  code: string;
  status: number;
}

export const handleApiError = (error: AxiosError): ApiError => {
  if (error.response) {
    const data = error.response.data as any;
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
    message: (error as any).message || 'An unexpected error occurred',
    code: 'UNKNOWN_ERROR',
    status: 0,
  };
};

export default api;
