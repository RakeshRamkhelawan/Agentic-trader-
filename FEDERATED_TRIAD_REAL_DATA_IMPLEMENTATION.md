# Federated Triad - Real Data Implementation Plan

## Current Problem Analysis

### Issue: Fake Data in Frontend
The `FederatedTriad.tsx` component currently uses **FAKE DATA** in several places:

1. **DEMO_STATE constant** (lines 96-118): Hardcoded agent data with fake metrics
2. **Derived calculations** (lines 154-231): Values calculated from portfolio positions, not real agent data
3. **Demo mode flag** (`isDemoMode`): Allows fallback to fake data

### Backend Reality
The backend provides **REAL** Federated Triad data via:
- `GET /api/v1/federated/state` - Returns actual council data from database
- Real agents from `trading_agents_v2`
- Real performance metrics from agent execution
- Real Chitta nodes from database tables
- Real deliberation records from `deliberation_records` table

---

## Implementation Strategy

### Phase 1: Update API Layer

#### 1.1 Create Federated API Client
```typescript
// lib/api/federated.ts
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
  deliberation_steps: DeliberationStep[];
}

export interface CouncilView {
  name: string;
  type: 'guna' | 'elemental' | 'graha' | 'mind' | 'body';
  status: 'active' | 'idle' | 'error';
  perspective: string;
  confidence: number;
  insights: string[];
  contradictions: string[];
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

export const federatedApi = {
  getState: async (): Promise<FederatedState> => {
    const response = await api.get<FederatedState>('/federated/state');
    return response.data;
  },
  
  getAgents: async (): Promise<{ agents: FederatedAgent[] }> => {
    const response = await api.get('/federated/agents');
    return response.data;
  },
  
  triggerSync: async () => {
    const response = await api.post('/federated/sync', {});
    return response.data;
  }
};
```

#### 1.2 Test: API Client
```typescript
// __tests__/api/federated.test.ts
describe('federatedApi', () => {
  it('should fetch real federated state from backend', async () => {
    const state = await federatedApi.getState();
    
    expect(state).toHaveProperty('coherence');
    expect(state).toHaveProperty('councils');
    expect(state).toHaveProperty('chitta');
    expect(state).toHaveProperty('latest_decision');
    expect(state.councils.length).toBeGreaterThan(0);
  });
  
  it('should have real council data with valid metrics', async () => {
    const state = await federatedApi.getState();
    
    state.councils.forEach(council => {
      expect(council.confidence).toBeGreaterThanOrEqual(0);
      expect(council.confidence).toBeLessThanOrEqual(1);
      expect(council.insights.length).toBeGreaterThan(0);
    });
  });
});
```

### Phase 2: Create Real Data Store

#### 2.1 Implement Federated Store
```typescript
// stores/federatedStore.ts
interface FederatedState {
  // Data
  coherence: CoherenceMetrics | null;
  councils: CouncilView[];
  chittaNodes: ChittaNode[];
  latestDecision: BuddhiDecision | null;
  deliberationSteps: DeliberationStep[];
  
  // Loading states
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  
  // Actions
  fetchState: () => Promise<void>;
  refresh: () => Promise<void>;
}

export const useFederatedStore = create<FederatedState>()((set, get) => ({
  coherence: null,
  councils: [],
  chittaNodes: [],
  latestDecision: null,
  deliberationSteps: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  
  fetchState: async () => {
    set({ isLoading: true, error: null });
    try {
      const state = await federatedApi.getState();
      set({
        coherence: state.coherence,
        councils: state.councils,
        chittaNodes: state.chitta.nodes,
        latestDecision: state.latest_decision,
        deliberationSteps: state.deliberation_steps,
        lastUpdated: new Date(),
        isLoading: false
      });
    } catch (err) {
      set({ 
        error: err instanceof Error ? err.message : 'Failed to fetch', 
        isLoading: false 
      });
    }
  },
  
  refresh: async () => {
    await get().fetchState();
  }
}));
```

#### 2.2 Test: Store State Management
```typescript
// __tests__/stores/federatedStore.test.ts
describe('federatedStore', () => {
  it('should fetch and store real federated data', async () => {
    const { result } = renderHook(() => useFederatedStore());
    
    await act(async () => {
      await result.current.fetchState();
    });
    
    expect(result.current.councils.length).toBeGreaterThan(0);
    expect(result.current.coherence).not.toBeNull();
    expect(result.current.lastUpdated).not.toBeNull();
  });
  
  it('should handle errors gracefully', async () => {
    server.use(
      rest.get('/api/v1/federated/state', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );
    
    const { result } = renderHook(() => useFederatedStore());
    
    await act(async () => {
      await result.current.fetchState();
    });
    
    expect(result.current.error).not.toBeNull();
    expect(result.current.isLoading).toBe(false);
  });
});
```

### Phase 3: Refactor FederatedTriad Component

#### 3.1 Remove All Fake Data
```typescript
// components/dashboard/FederatedTriad.tsx (REFACTORED)

// REMOVE: const DEMO_STATE: TriadState = { ... }
// REMOVE: const EMPTY_STATE: TriadState = { ... }
// REMOVE: const isDemoMode check
// REMOVE: All hardcoded agent calculations

// USE: Real data from useFederatedStore
export function FederatedTriad() {
  const { 
    coherence, 
    councils, 
    chittaNodes, 
    latestDecision, 
    deliberationSteps,
    isLoading,
    error,
    fetchState 
  } = useFederatedStore();
  
  // Auto-refresh every 5 seconds
  useEffect(() => {
    fetchState();
    const interval = setInterval(fetchState, 5000);
    return () => clearInterval(interval);
  }, [fetchState]);
  
  if (isLoading && !coherence) return <FederatedTriadSkeleton />;
  if (error) return <FederatedTriadError error={error} onRetry={fetchState} />;
  if (!coherence) return <FederatedTriadEmpty />;
  
  return (
    <div className="space-y-6">
      {/* Header with real coherence data */}
      <CoherenceHeader coherence={coherence} />
      
      {/* Councils with real data */}
      <CouncilsList councils={councils} />
      
      {/* Latest Decision */}
      {latestDecision && <LatestDecision decision={latestDecision} />}
      
      {/* Chitta Nodes */}
      <ChittaNodes nodes={chittaNodes} />
      
      {/* Deliberation Steps */}
      <DeliberationSteps steps={deliberationSteps} />
    </div>
  );
}
```

#### 3.2 Test: Component with Real Data
```typescript
// __tests__/components/FederatedTriad.test.tsx
describe('FederatedTriad', () => {
  it('should display real council data from backend', async () => {
    render(<FederatedTriad />);
    
    await waitFor(() => {
      expect(screen.getByText(/Federated Triad/i)).toBeInTheDocument();
    });
    
    // Should show real councils, not demo data
    await waitFor(() => {
      expect(screen.queryByText(/DEMO/i)).not.toBeInTheDocument();
    });
  });
  
  it('should auto-refresh data every 5 seconds', async () => {
    jest.useFakeTimers();
    render(<FederatedTriad />);
    
    await waitFor(() => {
      expect(federatedApi.getState).toHaveBeenCalledTimes(1);
    });
    
    act(() => {
      jest.advanceTimersByTime(5000);
    });
    
    await waitFor(() => {
      expect(federatedApi.getState).toHaveBeenCalledTimes(2);
    });
    
    jest.useRealTimers();
  });
});
```

### Phase 4: WebSocket Real-Time Updates

#### 4.1 Add WebSocket Support for Federated Data
```typescript
// hooks/useFederatedWebSocket.ts
export function useFederatedWebSocket() {
  const { updateFromWebSocket } = useFederatedStore();
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/federated`);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'coherence_update':
          updateFromWebSocket({ coherence: message.data });
          break;
        case 'council_update':
          updateFromWebSocket({ councils: message.data });
          break;
        case 'decision':
          updateFromWebSocket({ latestDecision: message.data });
          break;
        case 'chitta_update':
          updateFromWebSocket({ chittaNodes: message.data.nodes });
          break;
      }
    };
    
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    
    return () => ws.close();
  }, [updateFromWebSocket]);
  
  return { isConnected };
}
```

### Phase 5: Backend WebSocket Enhancement (if needed)

If the backend doesn't have WebSocket support for federated data:

```python
# backend/api/websockets.py
@router.websocket("/ws/federated")
async def federated_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Fetch real federated state
            state = await get_federated_state()
            await websocket.send_json({
                "type": "coherence_update",
                "data": state["coherence"]
            })
            await websocket.send_json({
                "type": "councils_update", 
                "data": state["councils"]
            })
            await asyncio.sleep(5)  # Update every 5 seconds
    except WebSocketDisconnect:
        pass
```

---

## Verification Checklist

### Data Integrity
- [ ] All council data comes from `/api/v1/federated/state`
- [ ] All coherence metrics are from backend calculations
- [ ] Chitta nodes are from database queries
- [ ] Buddhi decisions are from `buddhi_decisions` table
- [ ] No hardcoded values in component
- [ ] No calculated values from portfolio positions

### UI States
- [ ] Loading state shows skeleton
- [ ] Error state shows retry button
- [ ] Empty state when no data available
- [ ] Real-time updates visible
- [ ] Connection status indicator

### Testing
- [ ] Unit tests for API client
- [ ] Unit tests for store
- [ ] Integration tests for component
- [ ] E2E tests for full flow
- [ ] Mock server tests for error handling

---

## Migration Steps

### Step 1: Preparation
```bash
# Create backup of current component
cp FederatedTriad.tsx FederatedTriad.tsx.backup

# Create feature branch
git checkout -b feature/federated-real-data
```

### Step 2: Implementation Order
1. ✅ Create API client (`lib/api/federated.ts`)
2. ✅ Create store (`stores/federatedStore.ts`)
3. ✅ Write tests for API and store
4. ✅ Refactor component to use real data
5. ✅ Add WebSocket support (if backend ready)
6. ✅ Remove old DEMO_STATE and fake data
7. ✅ Update tests
8. ✅ Manual testing

### Step 3: Deployment
```bash
# Run tests
npm test -- FederatedTriad

# Build
npm run build

# Deploy
gh pr create --title "Federated Triad: Real Data Integration"
```

---

## Success Criteria

| Criteria | Before | After |
|----------|--------|-------|
| Data Source | DEMO_STATE constant | `/api/v1/federated/state` |
| Council Data | Hardcoded | From database |
| Coherence | Calculated from positions | From backend |
| Chitta Nodes | Fake records | From `chitta_nodes` table |
| Decisions | Simulated | From `buddhi_decisions` table |
| Auto-refresh | 3s polling | 5s polling + WebSocket |
| Demo Mode | Enabled | Removed |

---

## Files to Modify

1. `frontend/src/lib/api.ts` - Add federatedApi
2. `frontend/src/stores/federatedStore.ts` - New store (create)
3. `frontend/src/components/dashboard/FederatedTriad.tsx` - Refactor
4. `frontend/src/lib/config.ts` - Remove isDemoMode if unused elsewhere

## Estimated Effort

- **API Layer**: 2 hours
- **Store Implementation**: 3 hours
- **Component Refactor**: 4 hours
- **Testing**: 3 hours
- **WebSocket (optional)**: 4 hours
- **Total**: 12-16 hours

---

**Status**: Ready for Implementation  
**Priority**: HIGH (blocks production deployment)  
**Risk**: Medium (backend API exists but needs verification)
