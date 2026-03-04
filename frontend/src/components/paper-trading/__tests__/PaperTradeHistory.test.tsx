/**
 * PaperTradeHistory Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PaperTradeHistory } from '../PaperTradeHistory';
import usePaperTradingStore from '@/store/paper-trading';

vi.mock('@/store/paper-trading', () => ({
  default: vi.fn(),
}));

describe('PaperTradeHistory', () => {
  const mockTrades = [
    {
      id: '1',
      timestamp: '2026-03-02T10:00:00Z',
      symbol: 'BTC/EUR',
      side: 'buy',
      qty: 0.1,
      price: 50000,
      value: 5000,
      agent: 'MomentumAgent',
      exchange: 'Bitvavo',
    },
    {
      id: '2',
      timestamp: '2026-03-02T11:00:00Z',
      symbol: 'ETH/EUR',
      side: 'sell',
      qty: 1,
      price: 3000,
      value: 3000,
      agent: 'MeanReversionAgent',
      exchange: 'Bitvavo',
    },
  ];

  it('should display trade list', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      trades: mockTrades,
      isLoading: false,
    } as any);

    render(<PaperTradeHistory />);

    expect(screen.getByText('BTC/EUR')).toBeInTheDocument();
    expect(screen.getByText('ETH/EUR')).toBeInTheDocument();
    expect(screen.getByText('MomentumAgent')).toBeInTheDocument();
  });

  it('should show buy/sell indicators', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      trades: mockTrades,
      isLoading: false,
    } as any);

    render(<PaperTradeHistory />);

    expect(screen.getByText('BUY')).toBeInTheDocument();
    expect(screen.getByText('SELL')).toBeInTheDocument();
  });

  it('should format trade values correctly', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      trades: mockTrades,
      isLoading: false,
    } as any);

    render(<PaperTradeHistory />);

    expect(screen.getByText('€5,000.00')).toBeInTheDocument();
    expect(screen.getByText('€3,000.00')).toBeInTheDocument();
  });

  it('should show empty state when no trades', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      trades: [],
      isLoading: false,
    } as any);

    render(<PaperTradeHistory />);

    expect(screen.getByText('No trades yet')).toBeInTheDocument();
    expect(screen.getByText('Start trading to see your trade history')).toBeInTheDocument();
  });

  it('should show loading skeleton', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      trades: [],
      isLoading: true,
    } as any);

    const { container } = render(<PaperTradeHistory />);

    expect(container.querySelector('[data-testid="skeleton"]')).toBeInTheDocument();
  });
});
