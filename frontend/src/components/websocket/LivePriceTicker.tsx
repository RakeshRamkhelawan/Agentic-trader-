/**
 * LivePriceTicker Component
 * 
 * Real-time price display using WebSocket connection.
 * Shows connection status, current price, and 24h change.
 * 
 * @example
 * ```tsx
 * <LivePriceTicker symbol="BTC-EUR" />
 * <LivePriceTicker symbol="ETH-EUR" showOrderbook />
 * ```
 */

import { useState, useCallback } from 'react';
import { useChannel } from '@/context';

interface TickerData {
  symbol: string;
  bid: number;
  ask: number;
  last: number;
  volume_24h: number;
  change_24h: number;
  change_percent_24h: number;
  high_24h: number;
  low_24h: number;
  timestamp: string;
}

interface OrderbookData {
  bids: [string, string][];
  asks: [string, string][];
}

interface LivePriceTickerProps {
  /** Trading pair symbol (e.g., "BTC-EUR") */
  symbol: string;
  /** Show mini orderbook */
  showOrderbook?: boolean;
  /** Number of orderbook levels */
  orderbookLevels?: number;
}

export function LivePriceTicker({ 
  symbol, 
  showOrderbook = false,
  orderbookLevels = 5 
}: LivePriceTickerProps) {
  const [ticker, setTicker] = useState<TickerData | null>(null);
  const [orderbook, setOrderbook] = useState<OrderbookData | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Use global WebSocket context with automatic subscription management
  const { isConnected: isTickerConnected } = useChannel(
    `ticker.${symbol}`,
    useCallback((message: { data?: unknown }) => {
      if (message.data) {
        setTicker(message.data as TickerData);
        setLastUpdate(new Date());
      }
    }, [])
  );

  const { isConnected: isOrderbookConnected } = useChannel(
    `orderbook.${symbol}`,
    useCallback((message: { data?: unknown }) => {
      if (message.data) {
        setOrderbook(message.data as OrderbookData);
      }
    }, [])
  );

  // Connection is ready when ticker is connected (orderbook is optional)
  const isConnected = isTickerConnected && (!showOrderbook || isOrderbookConnected);

  // Note: useChannel handles automatic subscription/unsubscription
  // No manual subscribe/unsubscribe needed

  const formatPrice = (price: number | undefined) => {
    if (!price) return '---';
    return new Intl.NumberFormat('nl-NL', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: symbol.includes('BTC') ? 2 : 4
    }).format(price);
  };

  const formatPercent = (percent: number | undefined) => {
    if (!percent) return '---';
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
  };

  const getChangeColor = (value: number | undefined) => {
    if (!value) return 'text-gray-400';
    return value >= 0 ? 'text-green-500' : 'text-red-500';
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      {/* Header with connection status */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">{symbol}</h3>
        <div className="flex items-center gap-2">
          <span 
            className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}
            title={isConnected ? 'Connected' : 'Disconnected'}
          />
          <span className="text-xs text-gray-400">
            {isConnected ? 'Live' : 'Offline'}
          </span>
          {lastUpdate && (
            <span className="text-xs text-gray-500">
              {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Price display */}
      {ticker ? (
        <div className="space-y-2">
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">
              {formatPrice(ticker.last)}
            </span>
            <span className={`text-sm font-medium ${getChangeColor(ticker.change_percent_24h)}`}>
              {formatPercent(ticker.change_percent_24h)}
            </span>
          </div>

          {/* Bid/Ask spread */}
          <div className="flex gap-4 text-sm">
            <div>
              <span className="text-gray-500">Bid: </span>
              <span className="text-green-400">{formatPrice(ticker.bid)}</span>
            </div>
            <div>
              <span className="text-gray-500">Ask: </span>
              <span className="text-red-400">{formatPrice(ticker.ask)}</span>
            </div>
          </div>

          {/* 24h stats */}
          <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-gray-800 text-xs">
            <div>
              <div className="text-gray-500">24h High</div>
              <div className="text-white">{formatPrice(ticker.high_24h)}</div>
            </div>
            <div>
              <div className="text-gray-500">24h Low</div>
              <div className="text-white">{formatPrice(ticker.low_24h)}</div>
            </div>
            <div>
              <div className="text-gray-500">24h Vol</div>
              <div className="text-white">{ticker.volume_24h.toFixed(4)}</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-gray-500 text-center py-4">
          {isConnected ? 'Waiting for data...' : 'Connecting...'}
        </div>
      )}

      {/* Mini orderbook */}
      {showOrderbook && orderbook && (
        <div className="mt-4 pt-4 border-t border-gray-800">
          <h4 className="text-xs font-medium text-gray-400 mb-2">Orderbook</h4>
          <div className="grid grid-cols-2 gap-4 text-xs">
            {/* Asks (sells) - reversed to show highest ask at bottom */}
            <div className="space-y-1">
              <div className="text-red-400 font-medium mb-1">Asks</div>
              {orderbook.asks.slice(0, orderbookLevels).reverse().map(([price, amount], i) => (
                <div key={i} className="flex justify-between">
                  <span className="text-red-400">{parseFloat(price).toFixed(2)}</span>
                  <span className="text-gray-500">{parseFloat(amount).toFixed(4)}</span>
                </div>
              ))}
            </div>

            {/* Bids (buys) */}
            <div className="space-y-1">
              <div className="text-green-400 font-medium mb-1">Bids</div>
              {orderbook.bids.slice(0, orderbookLevels).map(([price, amount], i) => (
                <div key={i} className="flex justify-between">
                  <span className="text-green-400">{parseFloat(price).toFixed(2)}</span>
                  <span className="text-gray-500">{parseFloat(amount).toFixed(4)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default LivePriceTicker;
