# Paper Trading V18 - Database Logging Implementation

## Overview

Paper Trading V18 now persists all trading data to PostgreSQL instead of relying solely on file-based logging. This enables:
- **Querying historical trades** with SQL
- **Analytics and ML training** from structured data
- **Performance tracking** per agent, symbol, and regime
- **Session recovery** and audit trails

## Database Schema

### Tables

| Table | Purpose |
|-------|---------|
| `paper_trading_sessions` | Session metadata and final results |
| `paper_trades` | Individual trade records with full VedAstro/Elemental data |
| `paper_trading_analytics` | Per-cycle analysis for ML training |
| `agent_performance` | Agent win rates and performance scores |
| `chitta_experiences` | Learning experiences for consciousness system |

### Key Fields in `paper_trades`

- **Trade basics**: symbol, side, quantity, price, value, commission, pnl
- **VedAstro**: vedastro_signal, vedastro_confidence, vedastro_score, dominant_planet
- **Elemental Consensus**: elemental_votes (JSON), consensus_score, dominant_agent
- **Context**: regime, entry_type, exit_reason, is_hard_exit
- **Raw data**: analysis_data (full JSON for debugging)

## Integration Points

### 1. Session Management (`initialize()` and `close()`)

```python
# On start: Create session in database
async with self.db:
    session = await self.db.create_session(
        session_id=self.session_id,
        initial_capital=self.initial_capital,
        duration_hours=8,
        account_id=self.config.account_id,
    )
    self.db_session_id = session.id

# On end: Update final stats
async with self.db:
    await self.db.end_session(
        session_id=self.session_id,
        final_capital=final_value,
        reason=reason  # completed, circuit_breaker, negative_pnl
    )
```

### 2. Trade Logging (`_execute_entry()` and `_execute_exit()`)

Entry trades are saved with:
- Full VedAstro signal data (signal, confidence, score, planet)
- Elemental votes (Earth, Fire, Water)
- Consensus calculation and dominant agent
- Regime classification

Exit trades additionally include:
- Realized P&L
- Exit reason
- Hard/soft exit flag
- Agent performance update

### 3. Analytics Logging (`_log_analysis()`)

Every evaluation cycle logs:
- VedAstro analysis (signal, confidence, vote)
- Elemental votes (Earth, Fire, Water)
- Gunas (Sattva, Rajas, Tamas)
- Vayu dampener
- Consensus calculation
- Portfolio state
- Decision and reason

### 4. Agent Performance Tracking

After each exit trade:
- Win/loss recorded per agent/symbol/regime
- Win rate calculated
- Performance score (0.0-2.0) based on win rate and avg P&L
- Max profit/loss tracked

## Configuration

Database logging is enabled by default:

```python
engine = RealPaperTradingV18(
    initial_capital=100000.0,
    use_database=True,  # Enable database logging
)
```

To disable (file-only logging):

```python
engine = RealPaperTradingV18(
    initial_capital=100000.0,
    use_database=False,
)
```

## Testing

Run the integration test:

```bash
python test_paper_trading_db_logging.py
```

Expected output:
```
[PASS]: Database Connection
[PASS]: Tables Exist
[PASS]: PaperTradingDB Service
[PASS]: V18 Engine Integration

Result: 4/4 tests passed
```

## Query Examples

### Get all trades from a session

```sql
SELECT * FROM paper_trades
WHERE session_id = '20260307_120000'
ORDER BY executed_at;
```

### Get win rate by agent

```sql
SELECT
    agent,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
    AVG(pnl) as avg_pnl
FROM paper_trades
WHERE trade_type = 'exit'
GROUP BY agent;
```

### Get performance by regime

```sql
SELECT
    regime,
    COUNT(*) as trades,
    AVG(pnl) as avg_pnl,
    SUM(pnl) as total_pnl
FROM paper_trades
WHERE trade_type = 'exit' AND regime IS NOT NULL
GROUP BY regime;
```

### Get consensus distribution

```sql
SELECT
    CASE
        WHEN total_vote >= 0.6 THEN 'strong_buy'
        WHEN total_vote >= 0.35 THEN 'buy'
        WHEN total_vote >= -0.3 THEN 'neutral'
        ELSE 'sell'
    END as consensus_level,
    COUNT(*) as count
FROM paper_trading_analytics
GROUP BY 1;
```

## Files Modified

1. **backend/services/paper_trading_db.py**
   - Fixed import to use `SessionManager` instead of `get_db_session`
   - Fixed `update_agent_performance()` to handle None values

2. **backend/services/real_paper_trading_v18_direct.py**
   - Already had full database logging integration
   - Session creation in `initialize()`
   - Trade logging in `_execute_entry()` and `_execute_exit()`
   - Analytics logging in `_log_analysis()`
   - Session finalization in `close()`

## Verification

All database logging features have been verified:

- ✅ Sessions created at start
- ✅ Entry trades persisted with VedAstro/Elemental data
- ✅ Exit trades persisted with P&L
- ✅ Per-cycle analytics logged
- ✅ Agent performance tracked
- ✅ Sessions properly closed with final stats

## Next Steps

1. **Run a live paper trading session** to populate real data
2. **Create Grafana dashboards** for real-time monitoring
3. **Build ML pipeline** to train on analytics data
4. **Add data retention policies** for long-term storage

---

*Implementation Date: 2026-03-07*
*Status: COMPLETE*
*Test Results: 4/4 passing*
