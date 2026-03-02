# Federated Triad - Next Level Implementatie

> **Status:** Gecorrigeerde roadmap gebaseerd op repo analyse
> **Prioriteit:** Fix fundamentals → Bouw features → ML laatst

---

## 🚨 FASE 0: Fundamentals (Deze Week)

### 0.1 Repo Cleanup
```bash
python scripts/cleanup_repo.py
```

**Verplaatst:**
- `*backtest*.json` → `backtest_results/`
- `*.log` → `logs/`
- `bandit*.json` → `reports/`

### 0.2 .gitignore Update
```gitignore
# Data files
*.csv
*.json
!package.json
!tsconfig.json
!config.json

# Logs
*.log
debug_*.txt

# Backtest results
backtest_results/*.json
backtest_results/*.csv

# Temp
.tmp/
__pycache__/
```

---

## 🔧 FASE 1: Kalibreerde Market Data (Week 1)

### Doel: Emotion detection met échte drempels

**Probleem:** Hardcoded `0.05` en `0.3` drempels zijn willekeurig
**Fix:** Gebruik bestaande backtest data om percentiles te berekenen

```python
# backend/core/market_data/chitta_feed.py
import pandas as pd
import numpy as np
from pathlib import Path

class CalibratedThresholds:
    """
    Laadt historische backtest data en berekent gedegen drempels.
    """

    def __init__(self):
        self.thresholds = self._calibrate_from_backtests()

    def _calibrate_from_backtests(self) -> dict:
        """
        Analyseer alle ml_batch_*.json files om percentiles te berekenen.
        """
        all_volatilities = []
        all_imbalances = []

        for file in Path("backtest_results").glob("ml_batch_*.json"):
            with open(file) as f:
                data = json.load(f)

            for feature in data.get("ml_features", []):
                if "atr_pct" in feature:
                    all_volatilities.append(feature["atr_pct"])
                if "volume_ratio" in feature:
                    all_imbalances.append(feature["volume_ratio"] - 1.0)

        if not all_volatilities:
            # Fallback als er geen data is
            return {
                "capitulation_vol": 0.05,
                "euphoria_vol": 0.03,
                "extreme_imbalance": 0.3
            }

        vol_series = pd.Series(all_volatilities)
        imb_series = pd.Series(all_imbalances)

        return {
            # 90th percentile = extreme conditions
            "capitulation_vol": vol_series.quantile(0.90),
            "euphoria_vol": vol_series.quantile(0.80),
            "uncertainty_vol": vol_series.quantile(0.60),
            "extreme_imbalance": imb_series.quantile(0.90),
            "sample_size": len(vol_series)
        }

    def detect_emotion(self, volatility_1m: float, imbalance: float) -> str:
        """Kalibreerde emotion detection."""
        if volatility_1m > self.thresholds["capitulation_vol"] and imbalance < -0.2:
            return "Capitulation"
        elif volatility_1m > self.thresholds["euphoria_vol"] and imbalance > 0.2:
            return "Euphoria"
        elif volatility_1m > self.thresholds["uncertainty_vol"]:
            return "Uncertainty"
        return "Neutral"
```

### Implementatie Stappen:
1. **Dag 1:** Run cleanup script
2. **Dag 2:** Implementeer `CalibratedThresholds`
3. **Dag 3:** Test op paper trading data
4. **Dag 4:** Update ChittaMarketFeed
5. **Dag 5:** Documenteer kalibratie resultaten

---

## 🔧 FASE 2: Event-Driven Triad (Week 2)

### Doel: Sub-500ms latency, geen polling

**Huidig:** Frontend pollt elke 3s
**Target:** Redis Streams → WebSocket → UI in < 500ms

```python
# backend/events/triad_event_bus.py
import redis.asyncio as redis
import json
from datetime import datetime

class TriadEventBus:
    """
    Redis Streams gebaseerde event bus.

    Streams:
    - triad.deliberations: Council beslissingen
    - triad.decisions: Buddhi finale besluiten
    - triad.executions: Paper trading executions
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)

    async def publish_deliberation(self, council_type: str,
                                   perspective: str,
                                   confidence: float,
                                   reasoning: str):
        """Publiceer council deliberatie."""
        event = {
            "type": "council_deliberation",
            "council": council_type,
            "perspective": perspective,
            "confidence": confidence,
            "reasoning": reasoning,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.redis.xadd(
            "triad.deliberations",
            {"data": json.dumps(event)},
            maxlen=1000  # Houd laatste 1000 events
        )

    async def publish_decision(self, decision: dict):
        """Publiceer Buddhi beslissing."""
        await self.redis.xadd(
            "triad.decisions",
            {"data": json.dumps(decision)},
            maxlen=500
        )

    async def subscribe(self, stream: str, last_id: str = "$"):
        """Subscribe to events (voor WebSocket)."""
        while True:
            try:
                messages = await self.redis.xread(
                    {stream: last_id},
                    block=5000  # 5s timeout
                )

                for stream_name, events in messages:
                    for event_id, data in events:
                        yield json.loads(data[b"data"])
                        last_id = event_id

            except Exception as e:
                logger.error(f"Event subscription error: {e}")
                await asyncio.sleep(1)
```

### WebSocket Endpoint:
```python
# backend/api/websocket/triad_ws.py
from fastapi import WebSocket

@app.websocket("/ws/triad")
async def triad_websocket(websocket: WebSocket):
    await websocket.accept()

    event_bus = TriadEventBus()

    # Subscribe to all triad streams
    async for event in event_bus.subscribe("triad.decisions"):
        await websocket.send_json(event)
```

### Frontend WebSocket Client:
```typescript
// frontend/src/hooks/useTriadWebSocket.ts
export function useTriadWebSocket() {
  const [lastDecision, setLastDecision] = useState(null);
  const [latency, setLatency] = useState(0);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/triad');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const receivedAt = Date.now();
      const sentAt = new Date(data.timestamp).getTime();

      setLastDecision(data);
      setLatency(receivedAt - sentAt);
    };

    return () => ws.close();
  }, []);

  return { lastDecision, latency };
}
```

---

## 🔧 FASE 3: Intelligente Councils (Week 3-4)

### 3.1 Guna Council (Dynamisch)

```python
# backend/councils/guna_council_v2.py
import numpy as np
from dataclasses import dataclass

@dataclass
class GunaVector:
    sattva: float  # Harmonisch, balans
    rajas: float   # Actief, beweging
    tamas: float   # Traag, stagnatie

class DynamicGunaCouncil:
    """
    Bereken Guna balans dynamisch uit market data.
    Niet meer hardcoded 50/30/20!
    """

    def analyze(self, market_data: dict) -> GunaVector:
        """
        Bereken Guna scores uit marktmetrieken.
        """
        # Sattva = lage volatiliteit + hoge liquiditeit
        vol = market_data.get("volatility_1m", 0.02)
        spread = market_data.get("bid_ask_spread", 0.001)

        sattva_score = max(0, 1.0 - (vol / 0.05) - (spread / 0.002))

        # Rajas = momentum + volume
        momentum = abs(market_data.get("momentum_1d", 0))
        volume_ratio = market_data.get("volume_ratio", 1.0)

        rajas_score = min(1.0, (momentum * 20) + (volume_ratio - 1.0) * 0.5)

        # Tamas = lage volume + hoge spread
        if volume_ratio < 0.7 and spread > 0.002:
            tamas_score = 0.8
        else:
            tamas_score = 0.2

        # Normalize to sum to 1.0
        total = sattva_score + rajas_score + tamas_score
        return GunaVector(
            sattva=sattva_score / total,
            rajas=rajas_score / total,
            tamas=tamas_score / total
        )

    def get_perspective(self, guna: GunaVector, trend: float) -> tuple:
        """
        Bepaal perspectief gebaseerd op dominante Guna.
        """
        if guna.rajas > 0.5:
            # Actieve markt
            if trend > 0:
                return "bullish", guna.rajas
            else:
                return "bearish", guna.rajas

        elif guna.tamas > 0.4:
            # Stagnante markt
            return "neutral", 1 - guna.tamas  # Lage confidence

        else:
            # Sattva dominant = balans, wachten
            return "neutral", guna.sattva
```

### 3.2 Mind Council (Fear/Greed)

```python
# backend/councils/mind_council.py
class MindCouncil:
    """
    Analyseert marktpsychologie.
    """

    def calculate_fear_greed(self, market_data: dict) -> float:
        """
        Bereken fear/greed index (0-100).

        0 = Extreme Fear
        50 = Neutral
        100 = Extreme Greed
        """
        components = []

        # 1. Volatiliteit (hoge vol = fear)
        vol = market_data.get("volatility_1m", 0.02)
        vol_score = max(0, 100 - (vol * 2000))  # 5% vol = 0 score
        components.append((vol_score, 0.3))

        # 2. Volume spike (hoge volume = greed of panic)
        vol_ratio = market_data.get("volume_ratio", 1.0)
        if vol_ratio > 2.0:
            # Extreme volume kan beide zijn, kijk naar prijsrichting
            price_change = market_data.get("momentum_1d", 0)
            if price_change > 0:
                volume_score = 80  # Greed
            else:
                volume_score = 20  # Fear
        else:
            volume_score = 50
        components.append((volume_score, 0.2))

        # 3. Order flow imbalance
        imbalance = market_data.get("imbalance", 0)
        imbalance_score = 50 + (imbalance * 50)  # -1 to 1 → 0 to 100
        components.append((imbalance_score, 0.3))

        # 4. Bid-ask spread (hoge spread = fear)
        spread = market_data.get("bid_ask_spread", 0.001)
        spread_score = max(0, 100 - (spread / 0.001) * 50)
        components.append((spread_score, 0.2))

        # Weighted average
        total_score = sum(score * weight for score, weight in components)
        total_weight = sum(weight for _, weight in components)

        return min(100, max(0, total_score / total_weight))

    def get_perspective(self, fear_greed: float) -> tuple:
        """
        Contrarian strategie: extreme waarden = reversal signal.
        """
        if fear_greed < 20:
            return "bullish", 0.7, "Extreme fear - potential bottom"
        elif fear_greed > 80:
            return "bearish", 0.6, "Extreme greed - risk of reversal"
        elif fear_greed < 40:
            return "neutral", 0.5, "Fear present - caution"
        elif fear_greed > 60:
            return "neutral", 0.5, "Greed present - caution"
        else:
            return "neutral", 0.6, "Balanced sentiment"
```

---

## 🔧 FASE 4: Buddhi Reflectie (Week 5)

### Fix voor Lookahead Bias

```python
# backend/core/reflection/buddhi_reflection.py
import numpy as np
from datetime import timedelta

class BuddhiReflection:
    """
    Reflectie op beslissingen met robuuste metrics.
    """

    def evaluate_decision(self, decision, price_history: list) -> dict:
        """
        Evalueer een beslissing over meerdere tijdshorizons.

        Niet alleen kijken naar 1 uur later, maar naar:
        - Sharpe ratio over 1h, 4h, 24h
        - Maximum drawdown
        - Win rate over vergelijkbare setups
        """
        if len(price_history) < 24:  # Need 24h of data
            return {"status": "insufficient_data"}

        entry_price = decision["price"]

        # Calculate returns at different horizons
        returns_1h = (price_history[1] - entry_price) / entry_price
        returns_4h = (price_history[4] - entry_price) / entry_price if len(price_history) >= 4 else None
        returns_24h = (price_history[24] - entry_price) / entry_price if len(price_history) >= 24 else None

        # Adjust for action direction
        if decision["action"] == "sell":
            returns_1h = -returns_1h
            if returns_4h:
                returns_4h = -returns_4h
            if returns_24h:
                returns_24h = -returns_24h

        # Calculate metrics
        returns = [r for r in [returns_1h, returns_4h, returns_24h] if r is not None]

        if not returns:
            return {"status": "error", "reason": "no_returns"}

        avg_return = np.mean(returns)
        sharpe_proxy = avg_return / (np.std(returns) + 1e-8)
        max_drawdown = min(returns)  # Worst return

        # Decision quality score
        if sharpe_proxy > 1.0:
            quality = "excellent"
        elif sharpe_proxy > 0.5:
            quality = "good"
        elif sharpe_proxy > 0:
            quality = "acceptable"
        else:
            quality = "poor"

        return {
            "status": "evaluated",
            "quality": quality,
            "sharpe_proxy": sharpe_proxy,
            "avg_return": avg_return,
            "max_drawdown": max_drawdown,
            "returns_1h": returns_1h,
            "returns_4h": returns_4h,
            "returns_24h": returns_24h
        }
```

---

## 🔧 FASE 5: Episodic Memory (Week 6-7)

### pgvector Setup

```sql
-- migration: add pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Episodic memory table
CREATE TABLE episodic_memory (
    id SERIAL PRIMARY KEY,
    embedding vector(128),  -- Chitta state embedding
    market_context JSONB,   -- Volledige marktcontext
    decision JSONB,         -- Buddhi beslissing
    outcome JSONB,          -- Evaluatie resultaat
    pnl DECIMAL(20, 8),     -- P&L
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    session_id VARCHAR(64)  -- Paper trading session
);

-- Index voor similarity search
CREATE INDEX ON episodic_memory USING ivfflat (embedding vector_cosine_ops);
```

### Memory System:

```python
# backend/core/memory/episodic_memory.py
import pgvector.asyncpg

class EpisodicMemory:
    """
    Sla trading episodes op en zoek vergelijkbare situaties.
    """

    async def store_episode(self, chitta_state: dict,
                          decision: dict,
                          outcome: dict):
        """Sla een episode op."""
        embedding = await self._create_embedding(chitta_state)

        await self.db.execute("""
            INSERT INTO episodic_memory
            (embedding, market_context, decision, outcome, pnl, session_id)
            VALUES ($1, $2, $3, $4, $5, $6)
        """,
            embedding,
            json.dumps(chitta_state),
            json.dumps(decision),
            json.dumps(outcome),
            outcome.get("pnl", 0),
            decision.get("session_id", "unknown")
        )

    async def find_similar_episodes(self, current_state: dict,
                                    limit: int = 5) -> list:
        """Vind vergelijkbare episodes."""
        current_embedding = await self._create_embedding(current_state)

        rows = await self.db.fetch("""
            SELECT market_context, decision, outcome, pnl,
                   embedding <=> $1 as distance
            FROM episodic_memory
            ORDER BY embedding <=> $1
            LIMIT $2
        """, current_embedding, limit)

        return [dict(row) for row in rows]

    async def calculate_karma_score(self, episodes: list) -> float:
        """
        Bereken gewogen succes rate van vergelijkbare episodes.
        """
        if not episodes:
            return 0.5  # Neutral

        total_pnl = sum(e["pnl"] for e in episodes)

        # Normalize to 0-1 score
        if total_pnl > 0.1:
            return min(1.0, 0.5 + total_pnl)
        elif total_pnl < -0.1:
            return max(0.0, 0.5 + total_pnl)
        else:
            return 0.5
```

---

## 🔧 FASE 6: A/B Testing Framework (Week 8)

### Doel: Valideer nieuwe Triad vs V17

```python
# backend/core/experimentation/ab_testing.py
from enum import Enum

class ExperimentVariant(Enum):
    V17_BASELINE = "v17_baseline"
    TRIAD_V2 = "triad_v2"

class ABTestFramework:
    """
    Run A/B tests tussen oude en nieuwe strategie.
    """

    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        self.v17_strategy = V17Strategy()
        self.triad_strategy = TriadV2Strategy()

    async def run_comparison(self, market_data: dict) -> dict:
        """
        Krijg beslissing van beide strategieën en vergelijk.
        """
        v17_decision = await self.v17_strategy.decide(market_data)
        triad_decision = await self.triad_strategy.decide(market_data)

        # Log beide
        await self._log_comparison(
            market_data=market_data,
            v17=v17_decision,
            triad=triad_decision
        )

        # In paper trading: voer beide uit met halve positie
        # In live: gebruik alleen de "control" variant (V17) voor nu

        return {
            "v17": v17_decision,
            "triad": triad_decision,
            "agreement": v17_decision["action"] == triad_decision["action"],
            "confidence_diff": triad_decision["confidence"] - v17_decision["confidence"]
        }
```

---

## 📊 Success Metrics & Monitoring

### Metrics Dashboard:

```python
# backend/core/telemetry/triad_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Latency
triad_latency = Histogram(
    'triad_decision_latency_seconds',
    'Time from market tick to Buddhi decision',
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Decision quality
decision_accuracy = Gauge(
    'triad_decision_accuracy_1h',
    'Percentage correcte voorspellingen over 1h'
)

# Council participation
council_contributions = Counter(
    'triad_council_contributions_total',
    'Aantal bijdragen per council',
    ['council_type']
)

# Coherence
coherence_score = Gauge(
    'triad_council_coherence',
    'Mate van overeenstemming tussen councils'
)
```

### Targets:

| Metric | Huidig | Target | Timeline |
|--------|--------|--------|----------|
| Decision Latency | ∞ | < 500ms | Week 2 |
| Coherence Accuracy | 0% | > 70% | Week 4 |
| A/B Test Win Rate | N/A | > 52% vs V17 | Week 8 |
| WebSocket Latency | 3000ms | < 200ms | Week 2 |
| Council Coverage | 1/5 | 3/5 | Week 4 |

---

## 🚀 Implementatie Checklist

### Week 1:
- [ ] Repo cleanup
- [ ] CalibratedThresholds implementeren
- [ ] Kalibratie test run
- [ ] Documentatie update

### Week 2:
- [ ] Redis Streams setup
- [ ] WebSocket endpoint
- [ ] Frontend WebSocket client
- [ ] Latency monitoring

### Week 3:
- [ ] DynamicGunaCouncil
- [ ] MindCouncil
- [ ] Event integratie
- [ ] Unit tests

### Week 4:
- [ ] Buddhi Reflection fix
- [ ] Council integration
- [ ] Coherence scoring
- [ ] E2E tests

### Week 5-6:
- [ ] pgvector migratie
- [ ] EpisodicMemory implementatie
- [ ] Karma scoring
- [ ] Memory retrieval tests

### Week 7-8:
- [ ] A/B framework
- [ ] Paper trading dual run
- [ ] Resultaten analyse
- [ ] Go/No-go beslissing

---

## ⚠️ Risico's & Mitigaties

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| VedAstro API blijft instabiel | Hoog | Graha Council als optional, niet blocking |
| Redis Streams te complex | Medium | Fallback naar simple pub/sub |
| Performance < 500ms niet haalbaar | Hoog | Async processing + caching |
| Council disagreement te hoog | Medium | Minimum confidence thresholds |
| Backtest overfitting | Hoog | A/B testing + walk-forward validatie |

---

**Volgende stap:** Laten we beginnen met Fase 0 (cleanup) + Fase 1 (kalibratie).
Wil je dat ik de cleanup script run en daarna de CalibratedThresholds implementeer?
