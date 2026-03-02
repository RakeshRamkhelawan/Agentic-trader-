# ReAct Agent Patterns

Implementation patterns for ReAct (Reasoning + Acting) agents in the Agentic Trader Platform.

## ReAct Pattern Structure

```
Observation → Thought → Action → Observation → ...
```

## Agent Lifecycle

```python
class MyAgent(BaseAgent):
    async def analyze(self, features, context):
        # 1. OBSERVE - Extract relevant data
        observation = self._observe(features)

        # 2. REASON - Think about what to do
        thought = await self._think(observation, context)

        # 3. ACT - Generate decision
        action = self._act(thought)

        # 4. PUBLISH - Share with event bus
        await self.publish_thought(thought, action)

        return action
```

## Common Agent Types

### Sentiment Agent
```python
class SentimentAgent(BaseAgent):
    async def analyze(self, features, context):
        headlines = features.get('news_headlines', [])

        # LLM reasoning
        sentiment = await self.ask_llm(
            f"Analyze sentiment: {headlines}",
            system_prompt="You are a financial sentiment analyzer."
        )

        return {
            'signal': self._parse_sentiment(sentiment),
            'confidence': 0.8,
            'reasoning': sentiment
        }
```

### Technical Agent
```python
class TechnicalAgent(BaseAgent):
    async def analyze(self, features, context):
        rsi = features.get('rsi', 50)
        price = features.get('price', 0)
        sma = features.get('sma_20', price)

        # Rule-based with LLM overlay
        if rsi < 30 and price > sma:
            signal = 'buy'
        elif rsi > 70 and price < sma:
            signal = 'sell'
        else:
            signal = 'hold'

        # Enhance with LLM reasoning
        reasoning = await self.ask_llm(
            f"Explain why {signal} makes sense given RSI={rsi}, price={price}"
        )

        return {'signal': signal, 'reasoning': reasoning}
```

## Agent Security Roles

```python
from backend.governance.agent_gatekeeper import AgentRole

AgentRole.UNTRUSTED   # New agents, limited permissions
AgentRole.STANDARD    # Vetted agents, normal permissions
AgentRole.PRIVILEGED  # System agents, elevated permissions
```

## Memory Management

```python
# Bounded history prevents OOM
self.reasoning_history: deque = deque(maxlen=1000)

# Store important decisions
self.reasoning_history.append({
    'timestamp': datetime.now(UTC).isoformat(),
    'signal': signal,
    'confidence': confidence,
    'pnl': realized_pnl  # Update after trade closes
})
```

## Testing Agents

```python
import pytest

@pytest.mark.asyncio
async def test_sentiment_agent():
    agent = SentimentAgent()

    features = {
        'symbol': 'BTC',
        'news_headlines': ['Bitcoin surges to new highs']
    }

    result = await agent.analyze(features, {})

    assert result['signal'] in ['buy', 'sell', 'hold']
    assert 0 <= result['confidence'] <= 1
```
