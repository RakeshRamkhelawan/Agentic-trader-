import apiClient from '../api-client';

export interface Asset {
  symbol: string;
  name: string;
  type: string;
}

export interface Ticker {
  symbol: string;
  price: number;
  change24h: number;
}

export interface OHLCV {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OrderRequest {
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit';
  quantity: number;
  price?: number;
}

export interface OrderResponse {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  status: string;
  quantity: number;
  price: number;
  created_at: string;
}

export const tradingApi = {
  getAssets: () => apiClient.get<Asset[]>('/api/v1/markets/assets'),
  getTicker: (symbol: string) => apiClient.get<Ticker>(`/api/v1/markets/ticker/${symbol}`),
  getOHLCV: (symbol: string) => apiClient.get<OHLCV[]>(`/api/v1/markets/ohlcv/${symbol}`),
  createOrder: (order: OrderRequest) => apiClient.post<OrderResponse>('/api/v1/orders', order),
  getOrders: () => apiClient.get<OrderResponse[]>('/api/v1/orders'),
  cancelOrder: (orderId: string) => apiClient.delete(`/api/v1/orders/${orderId}`),
};

export const portfolioApi = {
  getHoldings: () => apiClient.get('/api/v1/portfolio'),
  getHistory: () => apiClient.get('/api/v1/portfolio/history'),
  getPerformance: () => apiClient.get('/api/v1/portfolio/performance'),
};
