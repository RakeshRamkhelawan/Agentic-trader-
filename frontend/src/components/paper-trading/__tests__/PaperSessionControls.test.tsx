/**
 * PaperSessionControls Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PaperSessionControls } from '../PaperSessionControls';
import usePaperTradingStore from '@/store/paper-trading';

vi.mock('@/store/paper-trading', () => ({
  default: vi.fn(),
}));

describe('PaperSessionControls', () => {
  it('should show start button when session not running', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      isRunning: false,
      isStarting: false,
      isStopping: false,
      startSession: vi.fn(),
    } as any);

    render(<PaperSessionControls />);

    expect(screen.getByText('Start Session')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /start session/i })).toBeEnabled();
  });

  it('should show stop button when session running', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      isRunning: true,
      isStarting: false,
      isStopping: false,
      stopSession: vi.fn(),
    } as any);

    render(<PaperSessionControls />);

    expect(screen.getByText('Stop Session')).toBeInTheDocument();
  });

  it('should call startSession when start button clicked', async () => {
    const mockStart = vi.fn();
    vi.mocked(usePaperTradingStore).mockReturnValue({
      isRunning: false,
      isStarting: false,
      isStopping: false,
      startSession: mockStart,
    } as any);

    render(<PaperSessionControls />);

    fireEvent.click(screen.getByRole('button', { name: /start session/i }));

    expect(mockStart).toHaveBeenCalledWith({ duration: 8, capital: 10000 });
  });

  it('should call stopSession when stop button clicked', async () => {
    const mockStop = vi.fn();
    vi.mocked(usePaperTradingStore).mockReturnValue({
      isRunning: true,
      isStarting: false,
      isStopping: false,
      stopSession: mockStop,
    } as any);

    render(<PaperSessionControls />);

    fireEvent.click(screen.getByRole('button', { name: /stop session/i }));

    expect(mockStop).toHaveBeenCalled();
  });

  it('should disable buttons during loading', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      isRunning: false,
      isStarting: true,
      isStopping: false,
      startSession: vi.fn(),
    } as any);

    render(<PaperSessionControls />);

    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByText('Starting...')).toBeInTheDocument();
  });

  it('should show session info when running', () => {
    vi.mocked(usePaperTradingStore).mockReturnValue({
      isRunning: true,
      isStarting: false,
      isStopping: false,
      sessionId: 'session-123',
      startedAt: '2026-03-02T10:00:00Z',
      config: { duration: 8, capital: 10000 },
      stopSession: vi.fn(),
    } as any);

    render(<PaperSessionControls />);

    expect(screen.getByText('Session Active')).toBeInTheDocument();
    expect(screen.getByText('€10,000')).toBeInTheDocument();
    expect(screen.getByText('8 hours')).toBeInTheDocument();
  });
});
