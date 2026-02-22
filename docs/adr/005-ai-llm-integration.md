# ADR 005: AI/LLM Integration Strategy

## Status
Accepted

## Context

The platform differentiates through AI-powered trading analysis:
- VedAstro (astrological timing analysis)
- Elemental consensus (multi-factor scoring)
- Market sentiment analysis
- Natural language trade commands

We need a strategy for integrating LLMs that's cost-effective, reliable, and secure.

## Decision

We will use **DeepSeek API** as primary LLM provider with **MCP protocol** for tool integration.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AI/LLM INTEGRATION                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐  │
│  │ Claude       │      │ MCP Server   │      │ DeepSeek │  │
│  │ Desktop      │──────▶│ (Tools)      │──────▶│ API      │  │
│  │              │stdio │              │HTTP  │          │  │
│  └──────────────┘      └──────┬───────┘      └──────────┘  │
│                               │                             │
│                               │ Direct Import               │
│                               ▼                             │
│                      ┌─────────────────┐                    │
│                      │ Backend Services│                    │
│                      │ - VedAstro      │                    │
│                      │ - Backtest      │                    │
│                      │ - Trading       │                    │
│                      └─────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# backend/adapters/deepseek_client.py
class DeepSeekClient:
    """Client for DeepSeek LLM API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com"
    
    async def analyze_market_sentiment(
        self,
        symbol: str,
        news_items: list[str]
    ) -> SentimentAnalysis:
        """Analyze market sentiment using LLM."""
        
        prompt = f"""
        Analyze the sentiment for {symbol} based on these news items:
        {chr(10).join(f"- {item}" for item in news_items)}
        
        Provide:
        1. Overall sentiment (bullish/bearish/neutral)
        2. Confidence score (0-1)
        3. Key factors
        """
        
        response = await self._chat_completion(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return self._parse_sentiment(response)
```

### MCP Tools

```python
# backend/mcp_server/tools/vedastro_tool.py
@mcp.tool()
async def analyze_vedastro(
    symbol: str,
    date: str,
    location: str = "Amsterdam"
) -> VedAstroAnalysis:
    """
    Perform VedAstro analysis for trading timing.
    
    This tool calculates astrological indicators
    for optimal entry/exit timing.
    """
    # Call internal service directly
    from backend.services.consensus import VedAstroService
    
    service = VedAstroService()
    result = await service.calculate(
        symbol=symbol,
        date=datetime.fromisoformat(date),
        location=location
    )
    
    return VedAstroAnalysis(
        planetary_positions=result.positions,
        auspicious_periods=result.timings,
        recommendation=result.recommendation
    )
```

## Alternatives Considered

| Provider | Pros | Cons |
|----------|------|------|
| **DeepSeek (Chosen)** | Cost-effective, good reasoning | Newer player |
| OpenAI GPT-4 | Best quality | Expensive |
| Anthropic Claude | Excellent reasoning | API availability |
| Local (Ollama) | Free, private | Hardware requirements |

## Cost Management

| Strategy | Implementation |
|----------|----------------|
| Caching | Cache LLM responses for 1 hour |
| Batching | Batch multiple analyses in one call |
| Fallback | Use rules-based if LLM unavailable |
| Rate Limiting | 100 calls/minute per tenant |

## Data Privacy

- No PII sent to LLM APIs
- Market data only (public information)
- Results cached, not stored long-term
- Audit log of all AI decisions

## Consequences

### Positive
- **AI differentiation**: Unique trading signals
- **Natural language**: Users can ask questions
- **Extensible**: Easy to add new AI features
- **Cost controlled**: Caching and rate limiting

### Negative
- **Latency**: LLM calls take 1-3 seconds
- **Dependency**: External service reliability
- **Cost**: Scales with usage
- **Explainability**: AI decisions need transparency

## Related Decisions
- ADR 001: Dual Interface Architecture
- ADR 006: Redis Caching

## References
- [DeepSeek API](https://platform.deepseek.com/)
- [MCP Protocol](https://modelcontextprotocol.io/)
