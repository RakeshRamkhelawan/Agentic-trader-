# Paper Trading Page - TDD Implementation Plan

## Executive Summary

This document outlines a Test-Driven Development (TDD) approach to rebuild the Paper Trading page as a feature-complete, dashboard-equivalent interface with 100% backend integration.

---

## 1. Current State Analysis

### Existing Components
| Component | Purpose | Backend Integration |
|-----------|---------|---------------------|
| `LivePaperTrading.tsx` | Main paper trading interface | ✅ Live (WebSocket + REST) |
| `Dashboard.tsx` | Main dashboard with full features | ✅ Live (REST API) |
| `LivePaperTrading` (page) | Page wrapper | ✅ REST API |

### Gap Analysis
The current paper trading page lacks several dashboard features:
- ❌ No `OrderPanel` (manual trading)
- ❌ No `TradingChart` (price visualization)
- ❌ No `ActiveOrders` view (open orders management)
- ❌ No `AIAdvisor` component
- ❌ No `RecentActivity` feed
- ❌ No `TopMovers` market overview

---

## 2. TDD Methodology

### Red-Green-Refactor Cycle
1. **Red**: Write failing test for expected behavior
2. **Green**: Write minimal code to pass the test
3. **Refactor**: Optimize while keeping tests green

### Test Priority Matrix
| Priority | Feature | Backend Dependency |
|----------|---------|-------------------|
| P0 | Core session management | `POST /paper-trading/start`, `POST /paper-trading/stop` |
| P0 | Portfolio data display | WebSocket `portfolio` messages |
| P0 | Trade history | WebSocket `trade` messages |
| P1 | Manual order placement | `POST /trading/orders` |
| P1 | Active orders view | `GET /trading/orders/active` |
| P1 | Price chart | `GET /trading/candles/{symbol}` |
| P2 | AI Advisor | `POST /agents/chat` |
| P2 | Agent decisions | WebSocket `decision` messages |
| P3 | Market overview | `GET /trading/markets` |

---

## 3. Implementation Phases

### Phase 1: Foundation (Tests First)
**Goal**: Rebuild the core paper trading store with test coverage

#### 3.1.1 Test: Paper Trading Store Initialization
```typescript
// __tests__/stores/paperTradingStore.test.ts
describe('paperTradingStore', () => {
  it('should initialize with default state', () => {
    const { result } = renderHook(() => usePaperTradingStore());
    expect(result.current.isRunning).toBe(false);
    expect(result.current.portfolio).toBeNull();
    expect(result.current.trades).toEqual([]);
    expect(result.current.stats).toBeNull();
  });
});
```

#### 3.1.2 Implementation
```typescript
// stores/paperTradingStore.ts
interface PaperTradingState {
  isRunning: boolean;
  portfolio: Portfolio | null;
  trades: Trade[];
  stats: Stats | null;
  sessionId: string | null;
  startSession: (config: SessionConfig) => Promise<void>;
  stopSession: () => Promise<void>;
  fetchStatus: () => Promise<void>;
}
```

#### 3.1.3 Test: Session Lifecycle
```typescript
it('should start and stop paper trading session', async () => {
  const { result } = renderHook(() => usePaperTradingStore());

  // Start session
  await act(async () => {
    await result.current.startSession({ duration: 8, capital: 10000 });
  });

  expect(result.current.isRunning).toBe(true);
  expect(fetch).toHaveBeenCalledWith('/api/v1/paper-trading/start', {
    method: 'POST',
    body: JSON.stringify({ duration: 8, capital: 10000 })
  });

  // Stop session
  await act(async () => {
    await result.current.stopSession();
  });

  expect(result.current.isRunning).toBe(false);
});
```

### Phase 2: WebSocket Integration (Real-time Data)
**Goal**: Implement 100% real-time data streaming

#### 3.2.1 Test: WebSocket Connection
```typescript
// __tests__/hooks/usePaperTradingWebSocket.test.ts
describe('usePaperTradingWebSocket', () => {
  it('should connect when session is running', () => {
    const mockWS = new WebSocket('ws://localhost');
    const { result } = renderHook(() =>
      usePaperTradingWebSocket({ isRunning: true })
    );

    expect(result.current.isConnected).toBe(true);
  });

  it('should update trades on trade message', () => {
    const { result } = renderHook(() =>
      usePaperTradingWebSocket({ isRunning: true })
    );

    const tradeMessage = {
      type: 'trade',
      data: { symbol: 'BTC/EUR', side: 'buy', price: 50000, qty: 0.1 }
    };

    act(() => {
      mockWebSocket.triggerMessage(tradeMessage);
    });

    expect(result.current.trades[0]).toMatchObject(tradeMessage.data);
  });

  it('should update portfolio on portfolio message', () => {
    const portfolioMessage = {
      type: 'portfolio',
      data: { cash: 9000, total_value: 10000, pnl: 1000 }
    };

    act(() => {
      mockWebSocket.triggerMessage(portfolioMessage);
    });

    expect(result.current.portfolio).toMatchObject(portfolioMessage.data);
  });
});
```

#### 3.2.2 Implementation
```typescript
// hooks/usePaperTradingWebSocket.ts
export function usePaperTradingWebSocket({ isRunning }: { isRunning: boolean }) {
  const [isConnected, setIsConnected] = useState(false);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!isRunning) return;

    const ws = new WebSocket(`${WS_URL}/ws/paper-trading`);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      switch (message.type) {
        case 'trade':
          setTrades(prev => [message.data, ...prev].slice(0, 50));
          break;
        case 'portfolio':
          setPortfolio(message.data);
          break;
        case 'stats':
          // Update stats
          break;
      }
    };

    return () => ws.close();
  }, [isRunning]);

  return { isConnected, trades, portfolio };
}
```

### Phase 3: Order Management (Dashboard Parity)
**Goal**: Implement manual trading (same as dashboard)

#### 3.3.1 Test: Order Placement
```typescript
// __tests__/components/paper-trading/PaperOrderPanel.test.tsx
describe('PaperOrderPanel', () => {
  it('should place buy order via paper trading API', async () => {
    render(<PaperOrderPanel />);

    fireEvent.change(screen.getByLabelText('Symbol'), {
      target: { value: 'BTC/EUR' }
    });
    fireEvent.change(screen.getByLabelText('Amount'), {
      target: { value: '0.1' }
    });
    fireEvent.click(screen.getByText('Buy'));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/v1/trading/orders', {
        method: 'POST',
        body: expect.stringContaining('"side":"buy"')
      });
    });
  });
});
```

#### 3.3.2 Implementation
```typescript
// components/paper-trading/PaperOrderPanel.tsx
export function PaperOrderPanel() {
  const { isRunning } = usePaperTradingStore();
  const { createOrder } = useOrdersApi();

  const handleSubmit = async (values: OrderFormValues) => {
    if (!isRunning) {
      toast.error('Start paper trading session first');
      return;
    }
    await createOrder({
      symbol: values.symbol,
      side: values.side,
      type: values.type,
      amount: values.amount,
      price: values.price
    });
  };

  return (
    <OrderForm
      onSubmit={handleSubmit}
      disabled={!isRunning}
      mode="paper"
    />
  );
}
```

### Phase 4: Chart Integration
**Goal**: Add trading charts with real-time data

#### 3.4.1 Test: Chart Data Fetching
```typescript
// __tests__/components/paper-trading/PaperTradingChart.test.tsx
describe('PaperTradingChart', () => {
  it('should fetch candle data for selected symbol', async () => {
    render(<PaperTradingChart symbol="BTC/EUR" timeframe="1h" />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/trading/candles/BTC-EUR')
      );
    });
  });

  it('should display price data on chart', async () => {
    const mockCandles = [
      { time: 1234567890, open: 50000, high: 51000, low: 49000, close: 50500 }
    ];

    render(<PaperTradingChart symbol="BTC/EUR" />);

    await waitFor(() => {
      expect(screen.getByTestId('chart')).toBeInTheDocument();
    });
  });
});
```

### Phase 5: AI Integration
**Goal**: Add AI Advisor and Agent Decisions

#### 3.5.1 Test: AI Advisor in Paper Mode
```typescript
// __tests__/components/paper-trading/PaperAIAdvisor.test.tsx
describe('PaperAIAdvisor', () => {
  it('should get advice specific to paper trading context', async () => {
    render(<PaperAIAdvisor />);

    fireEvent.change(screen.getByPlaceholderText('Ask about your trades...'), {
      target: { value: 'Should I buy BTC now?' }
    });
    fireEvent.click(screen.getByText('Send'));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/v1/agents/chat', {
        method: 'POST',
        body: expect.stringContaining('paper trading')
      });
    });
  });
});
```

### Phase 6: Full Page Assembly
**Goal**: Combine all components into unified page

#### 3.6.1 Test: Page Layout
```typescript
// __tests__/pages/PaperTrading.test.tsx
describe('PaperTrading Page', () => {
  it('should render all dashboard-equivalent components', () => {
    render(<PaperTradingPage />);

    expect(screen.getByTestId('portfolio-stats')).toBeInTheDocument();
    expect(screen.getByTestId('trading-chart')).toBeInTheDocument();
    expect(screen.getByTestId('order-panel')).toBeInTheDocument();
    expect(screen.getByTestId('active-orders')).toBeInTheDocument();
    expect(screen.getByTestId('trade-history')).toBeInTheDocument();
    expect(screen.getByTestId('ai-advisor')).toBeInTheDocument();
    expect(screen.getByTestId('agent-status')).toBeInTheDocument();
  });

  it('should disable trading controls when session not running', () => {
    render(<PaperTradingPage />);

    expect(screen.getByTestId('order-panel')).toBeDisabled();
  });
});
```

---

## 4. Component Architecture

### 4.1 New Components Required
```
components/paper-trading/
├── PaperTradingContainer.tsx      # Main container with session logic
├── PaperPortfolioStats.tsx        # Portfolio value, P&L cards
├── PaperTradingChart.tsx          # OHLCV chart (reuses dashboard)
├── PaperOrderPanel.tsx            # Buy/sell form
├── PaperActiveOrders.tsx          # Open orders list
├── PaperTradeHistory.tsx          # Completed trades table
├── PaperAIAdvisor.tsx             # Chat interface
├── PaperAgentStatus.tsx           # Agent activity display
├── PaperMarketOverview.tsx        # Top movers/market data
├── PaperSessionControls.tsx       # Start/stop buttons
├── PaperVedicContext.tsx          # Vedic context panel (reuse)
└── index.ts                       # Barrel export
```

### 4.2 Store Integration
```typescript
// Integration with existing appStore
const usePaperTradingStore = create<PaperTradingState>()(
  persist(
    (set, get) => ({
      // Paper-trading specific state
      sessionId: null,
      isRunning: false,
      sessionConfig: null,

      // Reuse existing API methods
      startSession: async (config) => {
        const response = await api.post('/paper-trading/start', config);
        set({
          isRunning: true,
          sessionId: response.data.session_id,
          sessionConfig: config
        });
      },

      // Sync with main appStore for shared data
      syncWithAppStore: () => {
        const { portfolio, trades } = get();
        // Update appStore with paper trading data
      }
    })
  )
);
```

---

## 5. Backend API Contract

### Required Endpoints (Already Available)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/paper-trading/start` | POST | Start session |
| `/api/v1/paper-trading/stop` | POST | Stop session |
| `/api/v1/paper-trading/status` | GET | Session status |
| `/ws/paper-trading` | WebSocket | Real-time updates |
| `/api/v1/trading/orders` | POST | Place order |
| `/api/v1/trading/orders/active` | GET | Get open orders |
| `/api/v1/trading/candles/{symbol}` | GET | Chart data |
| `/api/v1/trading/markets` | GET | Market overview |
| `/api/v1/agents/chat` | POST | AI advisor |
| `/api/v1/agents/status` | GET | Agent status |

---

## 6. Testing Strategy

### 6.1 Unit Tests
```typescript
// Test coverage targets:
- Stores: 100% state transitions
- Hooks: 100% lifecycle and data flow
- Components: 80%+ render paths
- Utils: 100% edge cases
```

### 6.2 Integration Tests
```typescript
// Critical user journeys:
- User starts session → places order → sees trade → stops session
- WebSocket reconnection on network failure
- Session recovery on page refresh
- Simultaneous dashboard and paper trading usage
```

### 6.3 E2E Tests
```typescript
// Playwright/Cypress scenarios:
- Complete trading workflow
- WebSocket stress testing
- Mobile responsiveness
- Error state handling
```

---

## 7. Implementation Schedule

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Foundation | Store + Tests, WebSocket hook + Tests |
| 2 | Core UI | Session controls, Portfolio stats, Trade history |
| 3 | Trading | Order panel, Active orders, Chart integration |
| 4 | AI Features | AI Advisor, Agent decisions, Market overview |
| 5 | Polish | E2E tests, Performance optimization, Bug fixes |

---

## 8. Acceptance Criteria

### 8.1 Functional Requirements
- [ ] User can start/stop paper trading session
- [ ] Real-time portfolio updates via WebSocket
- [ ] Real-time trade feed via WebSocket
- [ ] Manual order placement (buy/sell)
- [ ] Active orders view with cancel capability
- [ ] Price chart with symbol selection
- [ ] AI advisor context-aware responses
- [ ] Agent status and decision display
- [ ] Market overview (top movers)

### 8.2 Non-Functional Requirements
- [ ] WebSocket reconnection within 3 seconds
- [ ] Page load under 2 seconds
- [ ] 60 FPS chart rendering
- [ ] 100% test coverage for critical paths
- [ ] Zero hardcoded data
- [ ] Zero mock data in production

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| WebSocket instability | Implement exponential backoff reconnection |
| Backend API changes | Version API calls, add response validation |
| Performance issues | Virtualize trade lists, debounce chart updates |
| State synchronization | Use single source of truth pattern |

---

## 10. Appendix

### A. TypeScript Interfaces
```typescript
interface PaperTradingSession {
  id: string;
  started_at: string;
  config: SessionConfig;
  portfolio: Portfolio;
  trades: Trade[];
}

interface SessionConfig {
  duration: number;  // hours
  capital: number;   // initial capital
  symbols?: string[]; // allowed symbols
}
```

### B. WebSocket Message Types
```typescript
type WSMessage =
  | { type: 'trade'; data: Trade }
  | { type: 'portfolio'; data: Portfolio }
  | { type: 'stats'; data: Stats }
  | { type: 'decision'; data: AgentDecision }
  | { type: 'connected' };
```

---

**Document Version**: 1.0
**Last Updated**: 2026-03-02
**Author**: AI Assistant
**Status**: Ready for Implementation
