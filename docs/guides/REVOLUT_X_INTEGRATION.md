# Revolut X Integration Guide voor OODA Agents

Dit document beschrijft hoe je RevolutXAdapter integreert in de OODA agent pipeline.

## Overzicht

De RevolutXAdapter vervang de mock ExchangeAdapter in OrderExecutor, waardoor agents daadwerkelijk orders kunnen plaatsen op Revolut X.

```
DataScout → Analyst → Trader → [RiskManager] → OrderExecutor → RevolutXAdapter → Revolut X API
(Observe)   (Orient)  (Decide)  (Harmonize)      (Act)
```

## Quick Start

### 1. Test de Adapter Standalone

Eerst testen of de adapter werkt:

```bash
# Test RevolutXAdapter connectivity
python backend/integrations/test_revolut_x_connection.py

# Test RevolutXAdapter + OrderExecutor integration
python backend/integrations/test_revolut_executor.py
```

Verwachte output:
```
✅ Connected to Revolut X!
✅ OrderExecutor initialized with RevolutXAdapter
   Exchange: RevolutXAdapter
```

### 2. Integratie in OODALoopCoordinator

Pas `backend/orchestration/ooda_coordinator.py` aan:

```python
from backend.execution.revolut_x_adapter import RevolutXAdapter
from backend.execution.order_executor import OrderExecutor

class YourCoordinatorInitCode:
    async def initialize_agents(self):
        # 1. Create RevolutXAdapter
        revolut_adapter = RevolutXAdapter()

        # 2. Connect to Revolut X API
        await revolut_adapter.connect()

        # 3. Create OrderExecutor with real adapter
        order_executor = OrderExecutor(
            exchange_adapter=revolut_adapter,  # ← Real adapter instead of mock
            max_slippage_bps=50,  # 0.5% max slippage
            order_timeout=30      # 30 seconds timeout
        )

        # 4. Pass to OODALoopCoordinator
        coordinator = OODALoopCoordinator(
            data_scout=data_scout,
            analyst=analyst,
            trader=trader,
            risk_manager=risk_manager,
            # ... other agents ...
            order_executor=order_executor,  # ← Executor with Revolut X
            trading_mode=TradingMode.AUTO   # or TradingMode.NOTIFY_ONLY
        )

        return coordinator
```

### 3. Hele Flow Voorbeeld

```python
import asyncio
from backend.orchestration.ooda_coordinator import OODALoopCoordinator, TradingMode
from backend.execution.revolut_x_adapter import RevolutXAdapter
from backend.execution.order_executor import OrderExecutor
from backend.agents.data_scout_agent import DataScoutAgent
from backend.agents.analyst_agent import AnalystAgent
from backend.agents.trader_agent import TraderAgent
from backend.agents.risk_manager_agent import RiskManagerAgent

async def main():
    # Initialize RevolutXAdapter
    revolut_adapter = RevolutXAdapter()
    await revolut_adapter.connect()

    # Create OrderExecutor with Revolut X
    order_executor = OrderExecutor(
        exchange_adapter=revolut_adapter
    )

    # Initialize agents (example - adjust to your setup)
    data_scout = DataScoutAgent(...)
    analyst = AnalystAgent(...)
    trader = TraderAgent(...)
    risk_manager = RiskManagerAgent(...)

    # Create coordinator with real executor
    coordinator = OODALoopCoordinator(
        data_scout=data_scout,
        analyst=analyst,
        trader=trader,
        risk_manager=risk_manager,
        order_executor=order_executor,
        trading_mode=TradingMode.AUTO  # or NOTIFY_ONLY for manual approval
    )

    # Run OODA loop
    result = await coordinator.run_cycle(
        symbol="BTC/USDT",
        current_price=104000.0,
        strategy_id="momentum_v1"
    )

    print(f"Cycle result: {result}")

    # Cleanup
    await revolut_adapter.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## Trading Modes

### NOTIFY_ONLY Mode (Veilig voor Productie Start)

```python
coordinator = OODALoopCoordinator(
    # ... agents ...
    order_executor=order_executor,
    trading_mode=TradingMode.NOTIFY_ONLY  # ← Stop na RiskAssessment
)
```

**Gedrag:**
- OODA loop stopt na RiskAssessment
- Geen automatische order plaatsing
- Menselijke goedkeuring vereist via approval API
- Veilig voor productie testen

**Gebruik:**
- Eerste live testing
- High-value trades
- Nieuwe strategieën testen

### AUTO Mode (Volledig Geautomatiseerd)

```python
coordinator = OODALoopCoordinator(
    # ... agents ...
    order_executor=order_executor,
    trading_mode=TradingMode.AUTO  # ← Volledig automatisch
)
```

**Gedrag:**
- Volledige OODA cyclus zonder stops
- Automatische order plaatsing op Revolut X
- RiskManager kan nog steeds trades blokkeren
- CircuitBreaker safety mechanisme actief

**Gebruik:**
- Productie trading
- Low-latency strategieën
- Bewezen strategieën

## Order Flow Details

### OODA Schema → Revolut X Mapping

RevolutXAdapter mapt automatisch tussen OODA schema en Revolut X API:

| OODA Format | Revolut X Format | Voorbeeld |
|------------|------------------|-----------|
| Symbol: `BTC/USDT` | Symbol: `BTC-USD` | `/` → `-`, USDT → USD |
| Side: `"buy"` | Side: `OrderSide.BUY` | String → Enum |
| Type: `"limit"` | Type: `OrderType.LIMIT` | String → Enum |
| Status: `"pending"` | Status: `"new"` | OODA → Revolut X |

### ExecutionPlan → Order Flow

```python
# 1. Trader creates ExecutionPlan
execution_plan = ExecutionPlan(
    symbol="BTC/USDT",      # OODA format
    side="buy",
    order_type="limit",
    quantity=0.01,
    price=100000.0,
    agent_id="trader_001",
    strategy_id="momentum_v1"
)

# 2. OrderExecutor calls adapter
order = await executor.exchange.place_order(
    symbol="BTC/USDT",      # Still OODA format
    side="buy",
    order_type="limit",
    quantity=0.01,
    price=100000.0
)

# 3. RevolutXAdapter maps to Revolut X
await client.place_order(
    symbol="BTC-USD",       # Mapped to Revolut X format!
    side=OrderSide.BUY,     # Enum conversion
    quantity="0.01",        # String conversion
    price="100000.0",
    order_type=OrderType.LIMIT
)

# 4. Adapter maps response back to OODA
return Order(
    order_id="revx-12345",
    symbol="BTC/USDT",      # Back to OODA format
    side="buy",
    order_type="limit",
    status="pending",       # Mapped from Revolut X "new"
    quantity=0.01,
    price=100000.0
)
```

## Verificatie Log Berichten

### Succesvolle Integratie

Bij correcte setup zie je:

```
INFO - ✅ Using RevolutXAdapter for order execution
INFO - RevolutXAdapter connected to Revolut X API
INFO - Placing order: buy 0.01 BTC/USDT @ $100000.00
DEBUG - Mapping symbol: BTC/USDT → BTC-USD
INFO - Order placed on Revolut X: revx-order-12345
INFO - Order status: pending
```

### Mock Adapter Waarschuwing

Als je nog steeds mock gebruikt:

```
WARNING - ⚠️ Using MOCK ExchangeAdapter - orders will NOT be placed on real exchange!
```

**Actie:** Zorg dat je RevolutXAdapter injecteert via `exchange_adapter` parameter.

## Error Handling

RevolutXAdapter handled common errors automatisch:

### Timestamp Drift

```python
# Adapter past automatisch timestamp aan met -5000ms offset
# Voorkomt "timestamp in future" errors
```

### Symbol Conversie Fouten

```python
# Als symbool niet gemapped kan worden:
logger.error("Failed to map symbol: XYZ/ABC")
# Order wordt NIET geplaatst
```

### API Rate Limits

```python
# Revolut X: 1000 requests/minute per endpoint
# Adapter logt rate limit warnings
# Implementeer exponential backoff indien nodig
```

### Connection Errors

```python
try:
    await adapter.connect()
except Exception as e:
    logger.error(f"Failed to connect to Revolut X: {e}")
    # Fallback strategie:
    # 1. Retry met exponential backoff
    # 2. Gebruik mock adapter voor continuïteit
    # 3. Alert operations team
```

## Testing Strategie

### Phase 1: Connectivity Test (✅ COMPLETED)

```bash
python backend/integrations/test_revolut_x_connection.py
```

Verwacht: HTTP 200 OK, 0 active orders

### Phase 2: Executor Integration Test

```bash
python backend/integrations/test_revolut_executor.py
```

Verwacht: Adapter initialized, no errors

### Phase 3: Small Order Test (VOLGENDE STAP)

Uncomment execution block in `test_revolut_executor.py`:

```python
# UNCOMMENT THIS BLOCK:
outcome = await executor.execute_trade(execution_plan)
```

Test met:
- Limit order FAR from market (won't fill)
- Tiny quantity (0.0001 BTC ≈ $10)
- post_only flag (ensures no accidental fills)

### Phase 4: Full OODA Cycle Test

```bash
# Run complete OODA loop with Revolut X
python backend/orchestration/test_ooda_with_revolut.py
```

Test flow:
1. DataScout → Market observation
2. Analyst → Sentiment analysis
3. Trader → Trade proposal
4. RiskManager → Risk check
5. OrderExecutor → Revolut X order placement

### Phase 5: Production Rollout

1. Start in NOTIFY_ONLY mode
2. Monitor for 24 hours
3. Manually approve 10-20 trades
4. Verify no errors, slippage within limits
5. Switch to AUTO mode met lage position sizes
6. Gradually scale up

## Safety Checklist

Voordat je live gaat:

- [ ] `.env` geconfigureerd met Revolut X credentials
- [ ] `REVOLUT_SANDBOX=False` (productie mode)
- [ ] Ed25519 private key correct geïnstalleerd
- [ ] Test connectivity succesvol (`test_revolut_x_connection.py`)
- [ ] Test executor integration (`test_revolut_executor.py`)
- [ ] CircuitBreaker geïnstalleerd in coordinator
- [ ] RiskManager limits geconfigureerd
- [ ] Max position sizes ingesteld
- [ ] Slippage limits gedefinieerd (`max_slippage_bps`)
- [ ] Start in NOTIFY_ONLY mode
- [ ] Monitoring en alerting actief
- [ ] Kill switch gepland (hoe trading stoppen in noodgeval)

## Productie Configuratie

### Recommended Settings

```python
# Conservative settings voor eerste live trading
OrderExecutor(
    exchange_adapter=revolut_adapter,
    max_slippage_bps=50,      # 0.5% max slippage
    order_timeout=30,         # 30 seconds
)

# Risk limits
RiskManagerAgent(
    max_position_size=0.01,   # 0.01 BTC max
    max_daily_trades=10,      # 10 trades per dag
    max_drawdown_pct=2.0,     # 2% max drawdown
)

# Circuit breaker
CircuitBreaker(
    max_failures=3,           # 3 failures → pause
    reset_timeout=300,        # 5 min cooldown
)
```

### Environment Variables

```bash
# .env
REVOLUT_API_KEY="your-64-char-api-key"
REVOLUT_PRIVATE_KEY_PATH="C:/path/to/revolut_private.pem"
REVOLUT_SANDBOX=False  # Production mode

# Trading limits
MAX_POSITION_SIZE_BTC=0.01
MAX_DAILY_TRADES=10
MAX_SLIPPAGE_BPS=50
```

## Troubleshooting

### "Using MOCK ExchangeAdapter" warning

**Probleem:** OrderExecutor gebruikt nog steeds mock adapter

**Oplossing:**
```python
# WRONG:
executor = OrderExecutor()  # Gebruikt mock!

# RIGHT:
adapter = RevolutXAdapter()
await adapter.connect()
executor = OrderExecutor(exchange_adapter=adapter)  # Gebruikt Revolut X
```

### "Failed to connect to Revolut X"

**Check:**
1. `.env` file correct? (`REVOLUT_API_KEY`, `REVOLUT_PRIVATE_KEY_PATH`)
2. Private key file exists? (`revolut_private.pem`)
3. API key actief in Revolut X profile?
4. Internet connectivity?
5. Firewall blocking outbound HTTPS?

### "Symbol mapping failed"

**Probleem:** Symbol formaat niet herkend

**Ondersteunde formaten:**
- ✅ `BTC/USDT` → `BTC-USD`
- ✅ `ETH/USDT` → `ETH-USD`
- ❌ `BTC-PERP` (futures not supported)
- ❌ `BTCUSDT` (no separator)

**Custom mapping:**
```python
# backend/execution/revolut_x_adapter.py
def _map_symbol(self, symbol: str) -> str:
    # Add custom mapping hier
    if symbol == "CUSTOM/FORMAT":
        return "REVOLUT-FORMAT"
    # ... existing mapping logic
```

### Orders not appearing in Revolut X web UI

**Check:**
1. Order status: `pending` of `open`? (filled orders verdwijnen uit active orders)
2. Query historical orders: `client.get_active_orders()` toont alleen actieve orders
3. Order cancelled? Check logs voor cancellation messages
4. Wrong account? Verify API key corresponds to correct Revolut X account

## Next Steps

1. ✅ RevolutXAdapter created
2. ✅ OrderExecutor documentation updated
3. ✅ Test scripts created
4. 🔄 **JIJ BENT HIER**: Integreer in OODALoopCoordinator
5. ⏳ Test end-to-end flow
6. ⏳ Production rollout in NOTIFY_ONLY mode
7. ⏳ Scale to AUTO mode

## Support

Voor vragen over Revolut X integratie:
- Revolut X API Docs: https://developer.revolut.com/docs/x-api/
- Rate Limits: 1000 requests/min per endpoint
- Support: Revolut X dashboard op exchange.revolut.com

Voor vragen over OODA agent architectuur:
- Zie `docs/architecture/ooda_loop.md`
- Circuit breaker: `backend/governance/circuit_breaker.py`
- Risk manager: `backend/agents/risk_manager_agent.py`
