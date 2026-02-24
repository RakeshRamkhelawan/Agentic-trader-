/**
 * Global Type Definitions
 * 
 * Centralized TypeScript interfaces and types for the application.
 * Prevents duplication and ensures consistency across the codebase.
 */

// ============================================================================
// User & Authentication Types
// ============================================================================

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  displayName: string;
  avatar?: string;
  phone?: string;
  dateOfBirth?: string;
  country?: string;
  createdAt: Date;
  isKYCVerified?: boolean;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken?: string;
  expiresAt?: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

// ============================================================================
// KYC Types
// ============================================================================

export interface KYCData {
  status: 'not_started' | 'pending' | 'approved' | 'rejected';
  documentType?: 'passport' | 'id_card' | 'drivers_license';
  documentNumber?: string;
  documentExpiry?: string;
  address?: Address;
  occupation?: string;
  incomeRange?: string;
}

export interface Address {
  street: string;
  city: string;
  postalCode: string;
  country: string;
}

export interface KYCResponse {
  success: boolean;
  status: string;
  message?: string;
}

// ============================================================================
// Trading & Portfolio Types
// ============================================================================

export interface Trade {
  id: string;
  symbol: string;
  action: 'buy' | 'sell';
  quantity: number;
  price: number;
  total: number;
  timestamp: string;
  pnl?: number;
  status: 'pending' | 'completed' | 'failed';
}

export interface Position {
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
  unrealizedPnLPct: number;
}

export interface Portfolio {
  totalValue: number;
  cash: number;
  positions: Position[];
  dayPnL: number;
  totalPnL: number;
}

// ============================================================================
// VedAstro Types
// ============================================================================

export interface VedAstroSignal {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD' | 'STRONG_BUY' | 'STRONG_SELL';
  score: number;
  confidence: number;
  planetaryAlignment: PlanetaryAlignment;
  timestamp: string;
}

export interface PlanetaryAlignment {
  dominantPlanet: string;
  moonPhase: string;
  nakshatra?: string;
  aspects?: string[];
}

// ============================================================================
// Elemental Consensus Types
// ============================================================================

export interface ElementalConsensus {
  symbol: string;
  shouldEnter: boolean;
  consensusStrength: number;
  fireScore: number;
  earthScore: number;
  waterScore: number;
  airScore: number;
  timestamp: string;
}

export interface ElementalVotes {
  fire: number;
  earth: number;
  water: number;
  air: number;
}

// ============================================================================
// Backtest Types
// ============================================================================

export interface BacktestConfig {
  symbols: string[];
  startDate: string;
  endDate: string;
  initialCapital: number;
  enableParallel?: boolean;
  maxWorkers?: number;
}

export interface BacktestResult {
  backtestId: string;
  status: 'running' | 'completed' | 'failed';
  startDate: string;
  endDate: string;
  initialCapital: number;
  finalCapital: number;
  totalReturn: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  trades: Trade[];
  performance: BacktestPerformance;
}

export interface BacktestPerformance {
  sharpeRatio?: number;
  maxDrawdown?: number;
  volatility?: number;
  winRate: number;
  avgWin: number;
  avgLoss: number;
  profitFactor?: number;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, string[]>;
}

// ============================================================================
// WebSocket Types
// ============================================================================

export interface WebSocketMessage {
  type: string;
  payload: unknown;
  timestamp: string;
}

export interface MarketDataUpdate {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  timestamp: string;
}

// ============================================================================
// UI Types
// ============================================================================

export type Theme = 'dark' | 'light' | 'system';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
}

export interface SidebarItem {
  label: string;
  icon: string;
  path: string;
  badge?: number;
}
