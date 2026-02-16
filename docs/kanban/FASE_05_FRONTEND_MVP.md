# Fase 5: Frontend MVP

> **Prioriteit**: 🟡 HIGH
> **Afhankelijkheden**: Fase 1 (NavagrahaState API), Fase 2 (Auth0 React SDK), Fase 4 (WebSocket data)
> **Geschatte effort**: 7-10 dagen
> **Master document**: [SAMKHYA_MASTER_KANBAN_TDD.md](./SAMKHYA_MASTER_KANBAN_TDD.md)

---

## Overzicht

Next.js 15 frontend met Samkhya-specifieke visualisaties: Mahabhutas agent dashboard, Navagraha planetenkaart, real-time trading console, en explainability panel.

```
Frontend Architecture:
├── app/ (Next.js App Router)
│   ├── layout.tsx (Auth0Provider + QueryClientProvider)
│   ├── terminal/ (Trading Console)
│   ├── markets/ (Market Data)
│   ├── portfolio/ (Portfolio View)
│   └── history/ (Trade History)
├── components/
│   ├── dashboard/ (Mahabhutas + Navagraha + Coherence)
│   ├── trading/ (Chart, OrderBook, OrderTicket)
│   └── ui/ (Shadcn components)
├── hooks/ (WebSocket, Metrics)
├── lib/ (API clients, stores)
└── stores/ (Zustand: trading-store, ui-store)
```

---

## Bestaande Code Referenties

| Bestand | Status |
|---------|--------|
| [frontend/src/app/layout.tsx](../../frontend/src/app/layout.tsx) | Root layout ✅ |
| [frontend/src/app/providers.tsx](../../frontend/src/app/providers.tsx) | Provider setup ✅ |
| [frontend/src/components/dashboard/CoherenceAura.tsx](../../frontend/src/components/dashboard/CoherenceAura.tsx) | Aura visualisatie ✅ |
| [frontend/src/components/dashboard/TradingConsole.tsx](../../frontend/src/components/dashboard/TradingConsole.tsx) | Basis console ✅ |
| [frontend/src/components/dashboard/TradingView.tsx](../../frontend/src/components/dashboard/TradingView.tsx) | Chart component ✅ |
| [frontend/src/components/dashboard/OrderManager.tsx](../../frontend/src/components/dashboard/OrderManager.tsx) | Order management ✅ |
| [frontend/src/lib/api/websocket-client.ts](../../frontend/src/lib/api/websocket-client.ts) | WS client ✅ |
| [frontend/src/lib/stores/trading-store.ts](../../frontend/src/lib/stores/trading-store.ts) | Zustand store ✅ |
| [frontend/src/hooks/use-socket.ts](../../frontend/src/hooks/use-socket.ts) | Socket.io hook ✅ |

**Beschikbare libraries**:
- `@auth0/auth0-react` ✅ (al in package.json)
- `@tanstack/react-query` ✅
- `d3` ✅ (voor Navagraha chart)
- `lightweight-charts` ✅ (TradingView charts)
- `framer-motion` ✅ (animaties)
- `zustand` ✅ (state management)
- `react-grid-layout` ✅ (dashboard layout)
- `zod` ✅ (schema validatie)

---

## Taken & Microtaken

---

### TAAK 5.1: Mahabhutas Agent Dashboard

**Doel**: Visualisatie van 5 elementale agents met prana, guna, en health status.

**Bestanden te creëren**:
- `frontend/src/components/dashboard/MahabhutasPanel.tsx`
- `frontend/src/components/dashboard/ElementalAgentCard.tsx`
- `frontend/src/components/dashboard/PranaBar.tsx`
- `frontend/src/components/dashboard/GunaTriangle.tsx`
- `frontend/src/hooks/useAgentMetrics.ts`
- `frontend/src/tests/MahabhutasPanel.test.tsx`

---

#### Microtaak 5.1.1: ElementalAgentCard Component

**Masterprompt**:
```
Card voor elk elementaal agent (Ether, Air, Fire, Water, Earth).
Toont: agent naam + element symbool, huidige prana (0-100 bar),
guna verdeling (sattva/rajas/tamas triangel), health status indicator,
ruling graha naam + retrograde indicator.
Bestaand: glass-card.tsx component in frontend/src/components/ui/.
Styling: Tailwind CSS 4 + glass-card patroon.
Data via: useAgentMetrics() hook → backend /api/agents/metrics endpoint.
```

**Test FIRST**:
```typescript
// frontend/src/tests/MahabhutasPanel.test.tsx
import { render, screen } from '@testing-library/react';
import { MahabhutasPanel } from '../components/dashboard/MahabhutasPanel';

describe('MahabhutasPanel', () => {
  it('renders all 5 elemental agents', () => {
    // Happy: Alle 5 elementen zichtbaar
    render(<MahabhutasPanel />);
    expect(screen.getByText('Ether')).toBeInTheDocument();
    expect(screen.getByText('Air')).toBeInTheDocument();
    expect(screen.getByText('Fire')).toBeInTheDocument();
    expect(screen.getByText('Water')).toBeInTheDocument();
    expect(screen.getByText('Earth')).toBeInTheDocument();
  });

  it('shows prana bar for each agent', () => {
    // Happy: Prana bars zichtbaar
    render(<MahabhutasPanel />);
    const pranaBars = screen.getAllByRole('progressbar');
    expect(pranaBars).toHaveLength(5);
  });

  it('shows degraded status when prana low', () => {
    // Unhappy: Prana < 10 → degraded indicator
    // Mock agent met prana=5
  });

  it('handles API error gracefully', () => {
    // Unhappy: API fout → "Unable to load agent data" message
  });

  it('updates in real-time via WebSocket', () => {
    // Happy: WS update → card refreshes
  });
});
```

---

#### Microtaak 5.1.2: GunaTriangle SVG Component

**Masterprompt**:
```
Driehoek SVG die sattva/rajas/tamas verhoudingen toont.
Drie hoekpunten = drie gunas. Punt in driehoek = huidige balans.
Kleuren: Sattva=goud, Rajas=oranje, Tamas=donkerpaars.
Animatie: framer-motion transition bij state change.
Data: GunaModulation van NavagrahaState.
```

---

### TAAK 5.2: Navagraha Dashboard

**Doel**: Planetaire positie visualisatie, Rahu Kala indicator, Dasha progress.

**Bestanden te creëren**:
- `frontend/src/components/dashboard/NavagrahaPanel.tsx`
- `frontend/src/components/dashboard/PlanetaryChart.tsx` (D3 polar)
- `frontend/src/components/dashboard/RahuKalaIndicator.tsx`
- `frontend/src/components/dashboard/DashaProgress.tsx`
- `frontend/src/components/dashboard/HoraTimeline.tsx`
- `frontend/src/hooks/useNavagrahaState.ts`
- `frontend/src/tests/NavagrahaPanel.test.tsx`

---

#### Microtaak 5.2.1: PlanetaryChart (D3 Polar)

**Masterprompt**:
```
D3.js polar chart met 12 zodiac segmenten (30° elk).
9 planeten als punten op de cirkel op hun sidereal longitude.
Retrograde planeten: ← pijl indicator.
Aspecten: lijnen tussen planeten (kleur per type: trine=groen, square=rood).
Rahu/Ketu: stippellijnen (shadow planets).
Real-time update via WebSocket.
```

**Test FIRST**:
```typescript
describe('PlanetaryChart', () => {
  it('renders 12 zodiac segments', () => {
    // Happy: SVG bevat 12 arc segmenten
  });

  it('plots 9 planetary positions', () => {
    // Happy: 9 planet markers zichtbaar
  });

  it('shows retrograde indicator for Rahu', () => {
    // Happy: Rahu altijd met retrograde pijl
  });

  it('draws aspect lines between planets', () => {
    // Happy: Trine = groene lijn
  });

  it('handles empty state gracefully', () => {
    // Unhappy: Geen data → loading skeleton
  });
});
```

#### Microtaak 5.2.2: RahuKalaIndicator

**Masterprompt**:
```
Horizontal timeline bar voor huidige dag.
Rahu Kala periode gemarkeerd in rood.
Huidige tijd als lopende marker.
Trading gate status: OPEN (groen) / BLOCKED (rood).
Countdown timer als Rahu Kala nadert.
```

#### Microtaak 5.2.3: DashaProgress + HoraTimeline

**Masterprompt**:
```
DashaProgress: Horizontale progress bar van Mahadasha + Antardasha.
Labels: "Jupiter Mahadasha (30% — 5.2yr remaining)".
HoraTimeline: 24-uur bar met 24 hora segmenten.
Huidige hora highlighted. Ruling planet naam + symbool.
```

---

### TAAK 5.3: Auth0 React Integration + Trading Console

**Doel**: Auth0 login/logout, protected routes, real-time trading console.

**Bestanden te wijzigen**:
- `frontend/src/app/providers.tsx` (Auth0Provider toevoegen)
- `frontend/src/components/auth/protected-route.tsx` (Auth0 integratie)
- `frontend/src/components/dashboard/TradingConsole.tsx` (uitbreiden)

**Bestanden te creëren**:
- `frontend/src/lib/api/auth0-config.ts`
- `frontend/src/tests/auth0-integration.test.tsx`

---

#### Microtaak 5.3.1: Auth0Provider Setup

**Masterprompt**:
```
Wrap app in Auth0Provider (al geïnstalleerd: @auth0/auth0-react).
Config: domain, clientId, audience, redirectUri.
Protected route: redirect naar /login als niet geauthenticeerd.
Token injection in API calls via useAuth0().getAccessTokenSilently().
Bestaand: providers.tsx heeft al QueryClientProvider.
```

**Test FIRST**:
```typescript
describe('Auth0Integration', () => {
  it('redirects unauthenticated user to login', () => {
    // Happy: /terminal → redirect naar /login
  });

  it('renders page for authenticated user', () => {
    // Happy: Met geldig token → pagina laadt
  });

  it('injects token in API headers', () => {
    // Happy: API calls bevatten Authorization: Bearer <token>
  });

  it('handles expired token by refreshing', () => {
    // Unhappy: Verlopen token → silent refresh
  });
});
```

---

### TAAK 5.4: Explainability Panel

**Doel**: AI beslissing explainability — waarom is deze trade voorgesteld?

**Bestanden te creëren**:
- `frontend/src/components/dashboard/ExplainabilityPanel.tsx`
- `frontend/src/components/dashboard/DecisionTree.tsx`
- `frontend/src/hooks/useDecisionAudit.ts`
- `frontend/src/tests/ExplainabilityPanel.test.tsx`

---

#### Microtaak 5.4.1: Decision Audit Trail Viewer

**Masterprompt**:
```
Panel dat per trade beslissing uitlegt:
- OODA fase breakdown (Observe → Orient → Decide → Act)
- Navagraha context (welke planeten beïnvloedden de beslissing)
- Guna modulation effect (sattva/rajas/tamas shift)
- Elemental agent consensus (welke agents voor/tegen)
- 36-Tattva coherence score per laag
Data van: backend/governance/decision_audit.py API
```

**Test FIRST**:
```typescript
describe('ExplainabilityPanel', () => {
  it('shows OODA phase breakdown', () => {
    // Happy: O-O-D-A stappen zichtbaar
  });

  it('shows navagraha influence', () => {
    // Happy: Planetary context zichtbaar
  });

  it('handles missing audit trail', () => {
    // Unhappy: Geen audit data → "No explanation available"
  });

  it('links to detailed agent reports', () => {
    // Happy: Click → expandable agent detail
  });
});
```

**Taak-afronding integratie test**:
```typescript
describe('Integration: Frontend E2E', () => {
  it('login → dashboard → place trade → see explanation', async () => {
    // 1. Auth0 login
    // 2. Navigate naar /terminal
    // 3. Mahabhutas panel toont 5 agents
    // 4. Navagraha chart toont 9 planeten
    // 5. Place trade (paper)
    // 6. Explainability panel toont beslissing
  });
});
```

---

## Fase 5 Productie Test

```typescript
// frontend/src/tests/e2e/phase5_production.test.tsx

describe('Production Phase 5', () => {
  it('full frontend MVP smoke test', async () => {
    // 1. Auth0 login succesvol
    // 2. Dashboard laadt alle panels
    // 3. WebSocket datafeed actief
    // 4. Navagraha chart rendert
    // 5. Rahu Kala indicator zichtbaar
    // 6. Trading console functioneel
    // 7. Explainability panel beschikbaar
  });
});
```

---

## Kruisverwijzingen

- **← Fase 1**: NavagrahaState API endpoint (Taak 1.6 engine.assess())
- **← Fase 2**: Auth0 React SDK integratie (Taak 2.1)
- **← Fase 3**: Grafana dashboards embeddable (Taak 3.3)
- **← Fase 4**: WebSocket real-time data (Taak 4.1)
- **→ Fase 6**: Dashboard toont Karma feedback loop (Taak 6.1)
- **→ Fase 7**: MiFID II compliance indicators in UI (Taak 7.1)
