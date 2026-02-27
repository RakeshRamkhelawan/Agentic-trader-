# ToolBroker Symbiotic Integration Guide

Complete guide for integrating the ToolBroker with agents to enable external tool usage.

## Overview

The ToolBroker provides a symbiotic relationship between agents and external tools:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ SentimentAgent│  │ TechnicalAgent│  │ EnhancedSentimentAgent │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────────┘  │
└─────────┼─────────────────┼─────────────────────┼──────────────────┘
          │                 │                     │
          └─────────────────┼─────────────────────┘
                            │ Uses ToolBrokerClient
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      TOOLBROKER LAYER                                │
│                         (MCP Server)                                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────────┐  │
│  │  VedAstro    │  Elemental   │   External   │   Execution      │  │
│  │   Tools      │   Tools      │    Tools     │    Tools         │  │
│  ├──────────────┼──────────────┼──────────────┼──────────────────┤  │
│  │• Generate    │• Fire: Pos   │• Sentiment  │• Paper Trade    │  │
│  │  Signal      │  Size        │• Macro Data │• Close Position │  │
│  │• Get Dasha   │• Earth: Entry│• News       │• Get Positions  │  │
│  │• Get Transits│• Water: Regime│• Technical │• Trade History  │  │
│  └──────────────┴──────────────┴──────────────┴──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start the ToolBroker Service

```bash
# Start with MCP ToolBroker
docker-compose -f docker-compose.yml -f docker-compose.mcp.yml up -d

# Or use the Makefile (add 'mcp' target to Makefile)
make start-mcp
```

### 2. Verify ToolBroker Health

```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "server_name": "AgenticTraderBroker",
  "version": "1.0.0",
  "tools_available": 20
}
```

### 3. List Available Tools

```bash
curl http://localhost:8001/tools
```

### 4. Call a Tool

```bash
curl -X POST http://localhost:8001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "external__sentiment_analysis",
    "params": {"symbol": "BTC", "source": "news"}
  }'
```

## Using Tools in Agents

### Basic Usage

```python
from backend.agents.agent_with_tools import AgentWithTools

class MyAgent(AgentWithTools):
    async def analyze(self, features, context):
        # Call external sentiment analysis
        sentiment = await self.call_tool(
            "external__sentiment_analysis",
            {"symbol": "BTC", "source": "news"}
        )
        
        # Use VedAstro
        vedastro = await self.get_vedastro_signal("BTC", 45000)
        
        # Make decision
        if sentiment["score"] > 0.6 and vedastro["signal"] == "buy":
            return {"signal": "buy", "confidence": 0.8}
        
        return {"signal": "hold", "confidence": 0.5}
```

### Convenience Methods

The `AgentWithTools` base class provides convenience methods:

```python
# VedAstro
vedastro = await self.get_vedastro_signal(symbol, price)
dasha = await self.get_vedastro_dasha(symbol)

# Elemental
consensus = await self.get_elemental_consensus(fire, earth, water, air)
position_size = await self.calculate_position_size(symbol, portfolio, score, planet, history)
can_enter = await self.check_entry_allowed(symbol, trade_history)
regime = await self.get_market_regime()

# Execution
trade = await self.execute_paper_trade(symbol, "buy", qty, price, account)
```

### EnhancedSentimentAgent Example

```python
from backend.agents.enhanced_sentiment_agent import EnhancedSentimentAgent

agent = EnhancedSentimentAgent(
    tool_broker_url="http://localhost:8001"
)

result = await agent.analyze(
    features={
        "symbol": "BTC",
        "price": 45000,
        "history": [40000, 41000, 42000, ...]
    },
    context={"portfolio_value": 100000}
)

print(f"Signal: {result['signal']}")
print(f"Confidence: {result['confidence']}")
print(f"Reasoning: {result['reasoning']}")
```

## Available Tools

### VedAstro Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `vedastro__generate_signal` | Generate trading signal | `symbol`, `current_price` |
| `vedastro__get_dasha` | Get Dasha period | `symbol` |
| `vedastro__get_transits` | Get planetary transits | `symbol` |

### Elemental Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `elemental__fire_position_size` | Calculate position size | `symbol`, `portfolio_value`, `vedastro_score`, `dominant_planet`, `price_history` |
| `elemental__earth_entry_check` | Check if entry allowed | `symbol`, `trade_history` |
| `elemental__earth_exit_check` | Check if exit needed | `symbol`, `entry_date`, `current_date`, `entry_price`, `current_price`, `peak_price` |
| `elemental__water_regime_check` | Get market regime | `symbol`, `prices` |
| `elemental__ether_consensus` | Get elemental consensus | `fire_vote`, `earth_vote`, `water_vote`, `air_vote` |

### External Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `external__sentiment_analysis` | News/social sentiment | `symbol`, `source` (news/social/combined) |
| `external__macro_indicators` | Macro economic data | `indicator` (all/inflation/rates/employment/gdp) |
| `external__market_news` | Latest market news | `symbol`, `category`, `limit` |
| `external__technical_indicators` | Technical analysis | `symbol`, `price_history`, `indicators` |
| `external__market_correlation` | Correlation analysis | `symbol`, `benchmark`, `period` |

### Execution Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `execution__execute_paper_trade` | Execute paper trade | `symbol`, `action`, `quantity`, `current_price`, `account_id` |
| `execution__get_open_positions` | Get open positions | `account_id` |
| `execution__close_position` | Close position | `symbol`, `account_id`, `current_price` |
| `execution__get_trade_history` | Get trade history | `account_id`, `limit` |

## Environment Variables

Add these to your `.env` file:

```env
# ToolBroker Configuration
MCP_BROKER_URL=http://mcp-broker:8001
MCP_ENABLED=true

# External API Keys (optional, for real data)
DEEPSEEK_API_KEY=your_deepseek_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
NEWS_API_KEY=your_newsapi_key
```

## Architecture

### Communication Flow

```
Agent (Python)
    ↓
ToolBrokerClient (HTTP)
    ↓
MCP HTTP Server (FastAPI)
    ↓
MCP Tools (FastMCP)
    ↓
External APIs / Internal Logic
```

### Benefits

1. **Decoupling**: Agents don't need to know tool implementation
2. **Resilience**: Circuit breakers protect against failures
3. **Caching**: Tool results can be cached
4. **Monitoring**: All tool calls are logged and monitored
5. **Extensibility**: New tools can be added without changing agents

## Testing

```bash
# Test ToolBroker health
curl http://localhost:8001/health

# Test sentiment analysis
curl -X POST http://localhost:8001/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "external__sentiment_analysis", "params": {"symbol": "BTC"}}'

# Test technical indicators
curl -X POST http://localhost:8001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "external__technical_indicators",
    "params": {
      "symbol": "BTC",
      "price_history": [40000, 40500, 41000, 41500, 42000],
      "indicators": ["rsi", "sma"]
    }
  }'
```

## Troubleshooting

### ToolBroker Not Responding

```bash
# Check if container is running
docker ps | grep mcp-broker

# Check logs
docker logs agentic_trader_mcp_broker

# Restart
docker-compose restart mcp-broker
```

### Tool Call Fails

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check health
health = await agent.check_toolbroker_health()
print(health)
```

### Circuit Breaker Open

If a tool fails repeatedly, the circuit breaker opens:

```json
{
  "success": false,
  "error": "Circuit breaker is OPEN for tool: external__sentiment_analysis"
}
```

Wait 30 seconds for the circuit to close automatically.

## Next Steps

1. **Create Custom Tools**: Add new tools to `backend/mcp_broker/tools/`
2. **Extend Agents**: Create agents that combine multiple tools
3. **Add Caching**: Implement Redis caching for expensive tool calls
4. **Monitoring**: Add Prometheus metrics for tool usage

## API Reference

### HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/tools` | GET | List all tools |
| `/tools/call` | POST | Call a tool |
| `/tools/{name}` | GET | Get tool info |
| `/vedastro/signal` | POST | Convenience: VedAstro signal |
| `/elemental/consensus` | POST | Convenience: Elemental consensus |
| `/elemental/position-size` | POST | Convenience: Position sizing |

See `backend/api/mcp_api.py` for full API details.
