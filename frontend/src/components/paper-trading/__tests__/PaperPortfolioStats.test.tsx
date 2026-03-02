/**
 * PaperPortfolioStats Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PaperPortfolioStats } from '../PaperPortfolioStats';
import usePaperTradingStore from '@/store/paper-trading';

// Mock the store
vi.mock('@/store/paper-trading', () => ({
  default: vi.fn(),
}));

describe('PaperPortfolioStats', () => {
  it('should display portfolio value', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      portfolio: {
        cash: 5000,
        total_value: 15000,
        pnl: 500,
        pnl_percent: 3.33,
      },
      isLoading: false,
    } as any);

    render(<PaperPortfolioStats />);

    expect(screen.getByText('€15,000.00')).toBeInTheDocument();
    expect(screen.getByText('Portfolio Value')).toBeInTheDocument();
  });

  it('should display P&L with positive indicator', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      portfolio: {
        cash: 5000,
        total_value: 15000,
        pnl: 500,
        pnl_percent: 3.33,
      },
      isLoading: false,
    } as any);

    render(<PaperPortfolioStats />);

    expect(screen.getByText('+€500.00')).toBeInTheDocument();
    expect(screen.getByText('+3.33%')).toBeInTheDocument();
  });

  it('should display P&L with negative indicator', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      portfolio: {
        cash: 5000,
        total_value: 9500,
        pnl: -500,
        pnl_percent: -5,
      },
      isLoading: false,
    } as any);

    render(<PaperPortfolioStats />);

    expect(screen.getByText('-€500.00')).toBeInTheDocument();
    expect(screen.getByText('-5.00%')).toBeInTheDocument();
  });

  it('should display cash and buying power', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      portfolio: {
        cash: 5000,
        buying_power: 5000,
        total_value: 10000,
        pnl: 0,
        pnl_percent: 0,
      },
      isLoading: false,
    } as any);

    render(<PaperPortfolioStats />);

    expect(screen.getByText('€5,000.00')).toBeInTheDocument();
    expect(screen.getByText('Cash')).toBeInTheDocument();
  });

  it('should show skeleton loader when loading', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      portfolio: null,
      isLoading: true,
    } as any);

    const { container } = render(<PaperPortfolioStats />);

    expect(container.querySelector('[data-testid="skeleton"]')).toBeInTheDocument();
  });

  it('should display empty state when no portfolio', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      portfolio: null,
      isLoading: false,
    } as any);

    render(<PaperPortfolioStats />);

    expect(screen.getByText('No portfolio data')).toBeInTheDocument();
    expect(screen.getByText('Start a trading session to see your portfolio')).toBeInTheDocument();
  });

  it('should display active positions count', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      portfolio: {
        cash: 5000,
        positions: {
          'BTC/EUR': { symbol: 'BTC/EUR', quantity: 0.1 },
          'ETH/EUR': { symbol: 'ETH/EUR', quantity: 1 },
        },
        total_value: 10000,
        pnl: 0,
        pnl_percent: 0,
      },
      isLoading: false,
    } as any);

    render(<PaperPortfolioStats />);

    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Active Positions')).toBeInTheDocument();
  });
});
