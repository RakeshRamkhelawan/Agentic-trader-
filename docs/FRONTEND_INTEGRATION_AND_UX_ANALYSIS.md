# Frontend Integration & UX Analysis
## Samkhya Yoga Agentic Trader — Dashboard & Visualization Strategy

**Generated:** 2026-02-15  
**Document Version:** 1.0  
**Purpose:** Define frontend architecture and UX patterns for Samkhya philosophical concepts

---

## 1. Backend API Mapping for Frontend Requirements

### 1.1 Existing API Endpoints Analysis

Based on codebase analysis, the following endpoints are available:

#### Trading API (`backend/api/trading_api.py`)
```
```
GET  /trading/markets          → List available trading pairs
GET  /trading/candles/{symbol} → OHLCV historical data
GET  /trading/portfolio         → Current positions & balances
GET  /trading/history           → Trade history
POST /trading/orders            → Place new order
```
```

#### WebSocket API (`backend/api/websocket_endpoints.py`)
```
```
WS   /ws                        → Real-time updates
GET  /ws/stats                  → WebSocket connection stats
```
```

#### Analytics API (`backend/api/analytics_api.py`)
```
```
GET  /analytics/performance     → Performance metrics
GET  /analytics/metrics         → Trading metrics
```
```

### 1.2 Required New Endpoints for Navagraha Visualization

**Missing APIs that need to be created:**

```python
# backend/api/navagraha_api.py (NEW)
from fastapi import APIRouter, Depends
from datetime import datetime

router = APIRouter(prefix="/navagraha", tags=["navagraha"])

@router.get("/current-state")
async def get_current_navagraha_state():
    """
    Returns current Navagraha state for dashboard visualization.
    
    Response:
    {
        "planets": [
            {
                "name": "Sun",
                "longitude": 315.42,
                "latitude": 0.0,
                "speed": 1.01,
                "is_retrograde": false,
                "zodiac_sign": "Aquarius",
                "house": 10
            },
            ...9 planets
        ],
        "guna_ratios": {
            "sattva": 0.45,
            "rajas": 0.35,
            "tamas": 0.20
        },
        "rahu_kala": {
            "is_active": false,
            "start_time": "2026-02-15T13:30:00Z",
            "end_time": "2026-02-15T15:00:00Z",
            "remaining_minutes": 45
        },
        "current_dasha": {
            "planet": "Mars",
            "sub_period": "Mars-Rahu",
            "remaining_days": 187,
            "end_date": "2026-08-21"
        },
        "calculated_at": "2026-02-15T14:15:30Z"
    }
    """
    pass

@router.get("/planetary-aspects")
async def get_planetary_aspects():
    """
    Returns current planetary aspects (conjunctions, oppositions, trines, etc.)
    
    Response:
    {
        "aspects": [
            {
                "planet1": "Mars",
                "planet2": "Saturn",
                "aspect_type": "square",
                "angle": 90.5,
                "orb": 0.5,
                "strength": "strong"
            }
        ]
    }
    """
    pass

@router.get("/trading-gate-status")
async def get_trading_gate_status():
    """
    Returns whether trading is currently allowed based on Navagraha gates.
    
    Response:
    {
        "trading_allowed": true,
        "blocking_factors": [],
        "rahu_kala_active": false,
        "unfavorable_transits": []
    }
    """
    pass

# backend/api/ooda_api.py (NEW)
@router.get("/ooda/current-cycle")
async def get_current_ooda_cycle():
    """
    Returns current OODA cycle state for transparency dashboard.
    
    Response:
    {
        "cycle_id": "ooda-20260215-141530",
        "current_phase": "Orient",
        "phases": {
            "Observe": {
                "status": "completed",
                "duration_ms": 234,
                "data_collected": {
                    "market_data": true,
                    "sentiment": true,
                    "navagraha_state": true
                }
            },
            "Orient": {
                "status": "in_progress",
                "strategy_candidates": ["TrendFollowing", "Breakout"],
                "selected_strategy": "TrendFollowing",
                "reason": "Mars Dasha favors aggressive strategies"
            },
            "Decide": {"status": "pending"},
            "Act": {"status": "pending"}
        },
        "navagraha_influence": {
            "dasha_selected_strategy": true,
            "guna_modulated_risk": "pending"
        }
    }
    """
    pass

# backend/api/agents_api.py (NEW)
@router.get("/agents/status")
async def get_agent_status():
    """
    Returns status of all 5 elemental agents.
    
    Response:
    {
        "agents": [
            {
                "element": "ether",
                "name": "Orchestrator",
                "prana_level": 87.5,
                "active": true,
                "last_signal": "2026-02-15T14:10:00Z",
                "recent_contributions": 12
            },
            {
                "element": "air",
                "name": "Research",
                "prana_level": 45.2,
                "active": true,
                "last_signal": "2026-02-15T14:12:00Z",
                "recent_contributions": 8
            },
            ...5 agents
        ],
        "guna_influence": {
            "dominant_guna": "rajas",
            "prana_decay_rate": 0.03
        }
    }
    """
    pass
```

### 1.3 WebSocket Real-Time Updates

**Recommended WebSocket message structure:**

```javascript
// Client subscribes to channels
ws.send(JSON.stringify({
    "action": "subscribe",
    "channels": [
        "navagraha.state",
        "ooda.cycle",
        "agents.prana",
        "trades.execution",
        "guna.change"
    ]
}));

// Server pushes updates
{
    "channel": "navagraha.state",
    "timestamp": "2026-02-15T14:15:30Z",
    "data": {
        "guna_ratios": {
            "sattva": 0.45,
            "rajas": 0.35,
            "tamas": 0.20
        },
        "dominant_guna_changed": true,
        "previous_dominant": "sattva",
        "new_dominant": "rajas"
    }
}

{
    "channel": "ooda.cycle",
    "timestamp": "2026-02-15T14:16:00Z",
    "data": {
        "phase": "Decide",
        "risk_assessment": {
            "risk_score": 0.65,
            "guna_modulation": "rajas_increased_risk_tolerance"
        }
    }
}

{
    "channel": "agents.prana",
    "timestamp": "2026-02-15T14:16:10Z",
    "data": {
        "element": "fire",
        "prana_level": 42.0,
        "prana_change": -2.5,
        "warning": "low_prana"
    }
}
```

---

## 2. UX/UI Concept for Samkhya Context

### 2.1 Color Coding Strategy for Gunas

**Visual Language:**

| Guna | Primary Color | Secondary | Meaning | UI Application |
|------|---------------|-----------|---------|----------------|
| **Sattva** | Soft White/Gold `#F5F3E8` | Light Blue `#B8D4E8` | Purity, clarity, harmony | Borders when sattva dominant |
| **Rajas** | Vibrant Red `#E63946` | Orange `#F77F00` | Energy, passion, activity | Alert colors, active states |
| **Tamas** | Deep Grey `#495057` | Dark Blue `#2B2D42` | Inertia, darkness, resistance | Disabled states, warnings |

**Application Examples:**

```css
/* Guna-based component states */
.trading-signal.sattva-dominant {
    border-left: 4px solid #F5F3E8;
    background: linear-gradient(to right, #F5F3E8 0%, #FFFFFF 10%);
}

.trading-signal.rajas-dominant {
    border-left: 4px solid #E63946;
    background: linear-gradient(to right, #E63946 0%, #FFFFFF 10%);
    animation: pulse 2s ease-in-out infinite;
}

.trading-signal.tamas-dominant {
    border-left: 4px solid #495057;
    background: linear-gradient(to right, #495057 0%, #FFFFFF 10%);
    opacity: 0.7;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}
```

### 2.2 Navagraha Planetary Visualization

**Component: Zodiac Wheel with Real-Time Positions**

```typescript
// components/NavagrahaWheel.tsx
interface PlanetPosition {
    name: string;
    longitude: number; // 0-360 degrees
    isRetrograde: boolean;
    zodiacSign: string;
}

const NavagrahaWheel: React.FC<{planets: PlanetPosition[]}> = ({planets}) => {
    return (
        <div className="zodiac-wheel">
            {/* SVG circle divided into 12 zodiac signs */}
            <svg viewBox="0 0 400 400">
                {/* Zodiac background */}
                <circle cx="200" cy="200" r="180" fill="none" stroke="#ddd" strokeWidth="2"/>
                
                {/* 12 zodiac divisions */}
                {[...Array(12)].map((_, i) => (
                    <line
                        key={i}
                        x1="200"
                        y1="200"
                        x2={200 + 180 * Math.cos((i * 30 - 90) * Math.PI / 180)}
                        y2={200 + 180 * Math.sin((i * 30 - 90) * Math.PI / 180)}
                        stroke="#ddd"
                        strokeWidth="1"
                    />
                ))}
                
                {/* Planets */}
                {planets.map(planet => {
                    const angle = (planet.longitude - 90) * Math.PI / 180;
                    const x = 200 + 150 * Math.cos(angle);
                    const y = 200 + 150 * Math.sin(angle);
                    
                    return (
                        <g key={planet.name}>
                            <circle
                                cx={x}
                                cy={y}
                                r="8"
                                fill={getPlanetColor(planet.name)}
                            />
                            {planet.isRetrograde && (
                                <text x={x} y={y - 12} fontSize="12" fill="red">R</text>
                            )}
                            <text x={x} y={y + 20} fontSize="10">{planet.name}</text>
                        </g>
                    );
                })}
            </svg>
        </div>
    );
};
```

### 2.3 Rahu Kala Gate Visual Blocker

**Design Pattern:** Modal overlay when Rahu Kala active

```typescript
// components/RahuKalaGate.tsx
const RahuKalaGate: React.FC<{rahuKala: RahuKalaState}> = ({rahuKala}) => {
    if (!rahuKala.is_active) return null;
    
    return (
        <div className="rahu-kala-overlay">
            <div className="rahu-kala-modal">
                <div className="icon-warning">
                    <span role="img" aria-label="blocked">🛑</span>
                </div>
                <h2>Trading Blocked - Rahu Kala Active</h2>
                <p>
                    The inauspicious Rahu Kala period is currently active.
                    Trading will resume in:
                </p>
                <div className="countdown">
                    <CountdownTimer until={rahuKala.end_time} />
                </div>
                <div className="info">
                    <p>Rahu Kala: {rahuKala.start_time} - {rahuKala.end_time}</p>
                    <p>This gate ensures alignment with Vedic timing principles.</p>
                </div>
            </div>
        </div>
    );
};
```

**CSS Styling:**

```css
.rahu-kala-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(75, 0, 0, 0.85);
    backdrop-filter: blur(10px);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
}

.rahu-kala-modal {
    background: linear-gradient(135deg, #2b2d42 0%, #495057 100%);
    color: white;
    padding: 3rem;
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    text-align: center;
    max-width: 500px;
    border: 3px solid #8d99ae;
}

.countdown {
    font-size: 3rem;
    font-weight: bold;
    color: #e63946;
    margin: 2rem 0;
}
```

### 2.4 OODA Loop Transparency Dashboard

**Component: Real-Time OODA Phase Tracker**

```typescript
// components/OODATransparency.tsx
interface OODAPhase {
    name: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    duration_ms?: number;
    details?: any;
}

const OODATransparency: React.FC<{cycle: OODACycle}> = ({cycle}) => {
    return (
        <div className="ooda-transparency">
            <h3>OODA Cycle: {cycle.cycle_id}</h3>
            
            <div className="ooda-phases">
                {['Observe', 'Orient', 'Decide', 'Act'].map(phase => (
                    <div key={phase} className={`phase phase-${cycle.phases[phase].status}`}>
                        <div className="phase-header">
                            <h4>{phase}</h4>
                            <StatusBadge status={cycle.phases[phase].status} />
                        </div>
                        
                        {cycle.phases[phase].status === 'completed' && (
                            <div className="phase-details">
                                <p>Duration: {cycle.phases[phase].duration_ms}ms</p>
                                {phase === 'Orient' && cycle.phases[phase].selected_strategy && (
                                    <>
                                        <p>Strategy: {cycle.phases[phase].selected_strategy}</p>
                                        <p className="navagraha-influence">
                                            🌟 Selected based on {cycle.navagraha_influence.dasha} Dasha
                                        </p>
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>
            
            <div className="navagraha-influence-summary">
                <h4>Navagraha Influence on This Cycle</h4>
                <ul>
                    <li>
                        <input type="checkbox" checked={cycle.navagraha_influence.dasha_selected_strategy} readOnly />
                        Dasha influenced strategy selection
                    </li>
                    <li>
                        <input type="checkbox" checked={cycle.navagraha_influence.guna_modulated_risk} readOnly />
                        Guna modulated risk assessment
                    </li>
                    <li>
                        <input type="checkbox" checked={!cycle.navagraha_influence.rahu_kala_blocked} readOnly />
                        Rahu Kala gate check passed
                    </li>
                </ul>
            </div>
        </div>
    );
};
```

### 2.5 Agent Prana Visualization

**Component: Elemental Agent Status Cards**

```typescript
// components/AgentPranaCards.tsx
const AgentPranaCards: React.FC<{agents: Agent[]}> = ({agents}) => {
    const elementIcons = {
        ether: '🌌',
        air: '💨',
        fire: '🔥',
        water: '💧',
        earth: '🌍'
    };
    
    return (
        <div className="agent-prana-grid">
            {agents.map(agent => (
                <div key={agent.element} className={`agent-card element-${agent.element}`}>
                    <div className="agent-header">
                        <span className="element-icon">{elementIcons[agent.element]}</span>
                        <h4>{agent.name}</h4>
                    </div>
                    
                    <div className="prana-meter">
                        <div 
                            className="prana-fill" 
                            style={{
                                width: `${agent.prana_level}%`,
                                backgroundColor: getPranaColor(agent.prana_level)
                            }}
                        />
                        <span className="prana-value">{agent.prana_level.toFixed(1)}%</span>
                    </div>
                    
                    <div className="agent-stats">
                        <p>Status: {agent.active ? '✓ Active' : '✗ Inactive'}</p>
                        <p>Contributions: {agent.recent_contributions}</p>
                        <p>Last Signal: {formatTimeAgo(agent.last_signal)}</p>
                    </div>
                    
                    {agent.prana_level < 20 && (
                        <div className="warning-badge">⚠️ Low Prana</div>
                    )}
                </div>
            ))}
        </div>
    );
};

function getPranaColor(level: number): string {
    if (level > 70) return '#28a745'; // Green
    if (level > 40) return '#ffc107'; // Yellow
    if (level > 20) return '#fd7e14'; // Orange
    return '#dc3545'; // Red
}
```

---

## 3. Frontend Technical Architecture

### 3.1 Recommended Stack

**Framework:** Next.js 14+ (App Router)  
**Rationale:**
- Server-side rendering for SEO and performance
- API routes for BFF pattern (Backend For Frontend)
- Built-in optimizations (image, font, bundle)
- TypeScript support
- React Server Components for data fetching

**State Management:** Zustand + React Query  
**Rationale:**
- **Zustand:** Lightweight global state (user prefs, theme, auth)
- **React Query:** Server state management (caching, revalidation, real-time updates)
- Avoids Redux complexity

```typescript
// stores/navagrahaStore.ts (Zustand)
import create from 'zustand';

interface NavagrahaStore {
    currentState: NavagrahaState | null;
    setCurrentState: (state: NavagrahaState) => void;
}

export const useNavagrahaStore = create<NavagrahaStore>((set) => ({
    currentState: null,
    setCurrentState: (state) => set({ currentState: state }),
}));

// hooks/useNavagrahaState.ts (React Query)
import { useQuery } from '@tanstack/react-query';

export function useNavagrahaState() {
    return useQuery({
        queryKey: ['navagraha', 'current-state'],
        queryFn: async () => {
            const res = await fetch('/api/navagraha/current-state');
            return res.json();
        },
        refetchInterval: 60000, // Refetch every minute
        staleTime: 30000, // Consider stale after 30 seconds
    });
}
```

### 3.2 Real-Time Updates Pattern

**Hybrid Approach: WebSocket + React Query**

```typescript
// hooks/useRealtimeNavagraha.ts
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import useWebSocket from 'react-use-websocket';

export function useRealtimeNavagraha() {
    const queryClient = useQueryClient();
    
    const { lastJsonMessage } = useWebSocket('wss://api.example.com/ws', {
        onOpen: () => {
            // Subscribe to navagraha updates
            sendJsonMessage({
                action: 'subscribe',
                channels: ['navagraha.state', 'guna.change']
            });
        },
        shouldReconnect: () => true,
        reconnectAttempts: 10,
        reconnectInterval: 3000,
    });
    
    useEffect(() => {
        if (lastJsonMessage?.channel === 'navagraha.state') {
            // Invalidate React Query cache to trigger refetch
            queryClient.invalidateQueries(['navagraha', 'current-state']);
            
            // Or directly update cache
            queryClient.setQueryData(['navagraha', 'current-state'], lastJsonMessage.data);
        }
    }, [lastJsonMessage, queryClient]);
}
```

### 3.3 BFF Pattern vs Direct API Calls

**Recommendation:** BFF (Backend For Frontend) via Next.js API Routes

**Rationale:**
- **Security:** Hide backend API keys/tokens
- **Aggregation:** Combine multiple backend calls into single frontend request
- **Transformation:** Adapt backend responses to frontend needs
- **Rate Limiting:** Protect backend from frontend abuse

**Example BFF Route:**

```typescript
// app/api/dashboard/route.ts (Next.js 14 App Router)
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    // Aggregate data from multiple backend services
    const [navagraha, agents, ooda, portfolio] = await Promise.all([
        fetch('http://backend:8000/navagraha/current-state'),
        fetch('http://backend:8000/agents/status'),
        fetch('http://backend:8000/ooda/current-cycle'),
        fetch('http://backend:8000/trading/portfolio'),
    ]);
    
    const dashboard = {
        navagraha: await navagraha.json(),
        agents: await agents.json(),
        ooda: await ooda.json(),
        portfolio: await portfolio.json(),
        timestamp: new Date().toISOString(),
    };
    
    return NextResponse.json(dashboard);
}
```

**Frontend Usage:**

```typescript
// components/Dashboard.tsx
export default function Dashboard() {
    const { data, isLoading } = useQuery({
        queryKey: ['dashboard'],
        queryFn: async () => {
            const res = await fetch('/api/dashboard'); // BFF route
            return res.json();
        },
        refetchInterval: 30000, // 30 seconds
    });
    
    if (isLoading) return <Skeleton />;
    
    return (
        <>
            <NavagrahaWheel planets={data.navagraha.planets} />
            <AgentPranaCards agents={data.agents.agents} />
            <OODATransparency cycle={data.ooda} />
            <PortfolioSummary portfolio={data.portfolio} />
        </>
    );
}
```

### 3.4 Performance Optimization for High-Frequency Updates

**Strategy: Debounce & Throttle**

```typescript
// hooks/useThrottledWebSocket.ts
import { useEffect, useRef } from 'react';
import { throttle } from 'lodash';

export function useThrottledNavagrahaUpdates(onUpdate: (data: any) => void, delay: number = 1000) {
    const throttledUpdate = useRef(throttle(onUpdate, delay)).current;
    
    const { lastJsonMessage } = useWebSocket('wss://api.example.com/ws');
    
    useEffect(() => {
        if (lastJsonMessage?.channel === 'navagraha.state') {
            throttledUpdate(lastJsonMessage.data);
        }
    }, [lastJsonMessage, throttledUpdate]);
}
```

**Strategy: Virtual Scrolling for Trade History**

```typescript
// components/TradeHistoryTable.tsx
import { useVirtualizer } from '@tanstack/react-virtual';

export function TradeHistoryTable({ trades }: { trades: Trade[] }) {
    const parentRef = useRef<HTMLDivElement>(null);
    
    const virtualizer = useVirtualizer({
        count: trades.length,
        getScrollElement: () => parentRef.current,
        estimateSize: () => 50, // Each row ~50px
        overscan: 10,
    });
    
    return (
        <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
            <div style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }}>
                {virtualizer.getVirtualItems().map(virtualRow => (
                    <div
                        key={virtualRow.index}
                        style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: `${virtualRow.size}px`,
                            transform: `translateY(${virtualRow.start}px)`,
                        }}
                    >
                        <TradeRow trade={trades[virtualRow.index]} />
                    </div>
                ))}
            </div>
        </div>
    );
}
```

---

## 4. Wireframe Concepts

### 4.1 Main Trading Dashboard Layout

```
```
┌─────────────────────────────────────────────────────────────────┐
│ [Logo] Samkhya Trader            [User]  [Settings]  [Logout]  │
├───────────────────────────────────┬─────────────────────────────┤
│                                   │   Navagraha State           │
│   Portfolio Summary               │   ┌───────────────────┐     │
│   ┌─────────────────────────┐    │   │   Zodiac Wheel    │     │
│   │ Total Value: $125,450   │    │   │   (9 planets)     │     │
│   │ Today P&L:  +$2,340     │    │   └───────────────────┘     │
│   │ Win Rate:    58.3%      │    │                             │
│   └─────────────────────────┘    │   Guna Ratios:              │
│                                   │   Sattva: ████░░ 45%        │
│   Active Strategies               │   Rajas:  ███░░░ 35%        │
│   ┌─────────────────────────┐    │   Tamas:  ██░░░░ 20%        │
│   │ • TrendFollowing (Mars) │    │                             │
│   │ • Breakout (Rahu)       │    │   Current Dasha: Mars       │
│   └─────────────────────────┘    │   Rahu Kala: ✓ Inactive     │
├───────────────────────────────────┴─────────────────────────────┤
│   OODA Cycle Transparency                                       │
│   ┌─────────┬─────────┬─────────┬─────────┐                   │
│   │ Observe │ Orient  │ Decide  │   Act   │                   │
│   │   ✓     │   ⟳     │   ...   │   ...   │                   │
│   └─────────┴─────────┴─────────┴─────────┘                   │
│   🌟 Dasha influenced strategy selection                        │
├─────────────────────────────────────────────────────────────────┤
│   Elemental Agents                                              │
│   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                    │
│   │ 🌌  │ │ 💨  │ │ 🔥  │ │ 💧  │ │ 🌍  │                    │
│   │87.5%│ │45.2%│ │92.1%│ │66.8%│ │78.3%│                    │
│   └─────┘ └─────┘ └─────┘ └─────┘ └─────┘                    │
└─────────────────────────────────────────────────────────────────┘
```
```

### 4.2 Rahu Kala Blocker Modal (Overlay)

```
```
         ┌─────────────────────────────────┐
         │           🛑                     │
         │   Trading Blocked - Rahu Kala   │
         │                                 │
         │   The inauspicious Rahu Kala    │
         │   period is currently active.   │
         │   Trading will resume in:       │
         │                                 │
         │         ⏱️ 00:42:15              │
         │                                 │
         │   Rahu Kala: 13:30 - 15:00      │
         │                                 │
         │   This gate ensures alignment   │
         │   with Vedic timing principles. │
         │                                 │
         │      [View Documentation]       │
         └─────────────────────────────────┘
```
```

---

*End of Frontend Integration & UX Analysis Document*