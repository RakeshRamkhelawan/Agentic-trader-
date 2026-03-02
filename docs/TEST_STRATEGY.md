# Enhanced Test Strategy

**Generated:** 2026-02-14
**Version:** 1.0
**Purpose:** Comprehensive testing approach without mocking critical components

---

## 1. Testing Philosophy

### Core Principles

1. **No Mocking of Swiss Ephemeris:** Real calculations required for confidence
2. **Invariant-Driven Testing:** Use known astronomical facts as test oracles
3. **Contract Testing:** Validate external API integrations without mocks
4. **Integration-First:** Test component interactions before isolation
5. **Property-Based Testing:** Generate test cases from system properties

---

## 2. Invariant Testing for Swiss Ephemeris

### 2.1 Concept

Instead of mocking ephemeris calculations, test against known invariants:
- Rahu is ALWAYS retrograde
- 9 planets must ALWAYS be present
- Planetary longitudes must be in range [0, 360)
- Sun cannot be retrograde
- Moon's speed is predictable

### 2.2 Implementation

```python
import pytest
from datetime import datetime, timedelta
from backend.core.navagraha import NavagrahaCalculator

class TestNavagrahaInvariants:

    @pytest.fixture
    def calculator(self):
        return NavagrahaCalculator()

    def test_rahu_always_retrograde(self, calculator):
        for days_offset in range(0, 365, 10):
            test_date = datetime(2024, 1, 1) + timedelta(days=days_offset)
            state = calculator.calculate(test_date)

            assert state.planets['Rahu'].is_retrograde, \
                f"Rahu must always be retrograde, failed at {test_date}"

    def test_nine_planets_present(self, calculator):
        test_date = datetime.utcnow()
        state = calculator.calculate(test_date)

        expected_planets = {
            'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter',
            'Venus', 'Saturn', 'Rahu', 'Ketu'
        }

        assert set(state.planets.keys()) == expected_planets, \
            f"Expected 9 planets, got {len(state.planets)}: {list(state.planets.keys())}"

    def test_longitude_range_valid(self, calculator):
        test_date = datetime.utcnow()
        state = calculator.calculate(test_date)

        for planet_name, position in state.planets.items():
            assert 0 <= position.longitude < 360, \
                f"{planet_name} longitude {position.longitude} out of range [0, 360)"

    def test_sun_never_retrograde(self, calculator):
        for month in range(1, 13):
            test_date = datetime(2024, month, 15)
            state = calculator.calculate(test_date)

            assert not state.planets['Sun'].is_retrograde, \
                f"Sun cannot be retrograde, failed at {test_date}"

    def test_moon_speed_reasonable(self, calculator):
        test_date = datetime.utcnow()
        state = calculator.calculate(test_date)

        moon_speed = abs(state.planets['Moon'].speed)

        assert 11 <= moon_speed <= 15, \
            f"Moon speed {moon_speed} deg/day outside normal range [11, 15]"

    def test_calculation_consistency(self, calculator):
        test_date = datetime(2024, 6, 15, 12, 0, 0)

        state1 = calculator.calculate(test_date)
        state2 = calculator.calculate(test_date)

        for planet in state1.planets:
            assert abs(state1.planets[planet].longitude - state2.planets[planet].longitude) < 0.01, \
                f"Inconsistent calculation for {planet}"

    def test_rahu_ketu_opposition(self, calculator):
        test_date = datetime.utcnow()
        state = calculator.calculate(test_date)

        rahu_long = state.planets['Rahu'].longitude
        ketu_long = state.planets['Ketu'].longitude

        diff = abs(rahu_long - ketu_long)
        if diff > 180:
            diff = 360 - diff

        assert abs(diff - 180) < 5, \
            f"Rahu and Ketu must be ~180° apart, got {diff}°"

    @pytest.mark.parametrize("date_str,expected_sign", [
        ("2024-03-21", "Aries"),
        ("2024-06-21", "Gemini"),
        ("2024-09-23", "Virgo"),
        ("2024-12-21", "Sagittarius"),
    ])
    def test_sun_sign_at_equinoxes(self, calculator, date_str, expected_sign):
        test_date = datetime.fromisoformat(date_str)
        state = calculator.calculate(test_date)

        sun_sign = state.planets['Sun'].sign

        assert sun_sign == expected_sign, \
            f"Sun sign at {date_str} should be {expected_sign}, got {sun_sign}"
```

### 2.3 Property-Based Testing

```python
from hypothesis import given, strategies as st
from hypothesis import settings, Phase

class TestNavagrahaProperties:

    @given(st.datetimes(
        min_value=datetime(2000, 1, 1),
        max_value=datetime(2050, 12, 31)
    ))
    @settings(max_examples=200, phases=[Phase.generate, Phase.target])
    def test_calculation_never_fails(self, test_date):
        calculator = NavagrahaCalculator()

        state = calculator.calculate(test_date)

        assert state is not None
        assert len(state.planets) == 9
        assert state.timestamp == test_date

    @given(st.floats(min_value=-90, max_value=90))
    def test_latitude_valid_range(self, latitude):
        calculator = NavagrahaCalculator(latitude=latitude)
        state = calculator.calculate(datetime.utcnow())

        assert state is not None
```

---

## 3. Integration Test Patterns for OODA Loop

### 3.1 Full Cycle Integration Test

```python
import pytest
import asyncio
from backend.orchestration.ooda_coordinator import OODACoordinator
from backend.core.navagraha import NavagrahaService

@pytest.mark.integration
@pytest.mark.asyncio
class TestOODAIntegration:

    @pytest.fixture
    async def coordinator(self):
        navagraha_service = NavagrahaService()
        market_service = MarketDataService()
        sentiment_service = SentimentService()

        coordinator = OODACoordinator(
            navagraha_service=navagraha_service,
            market_service=market_service,
            sentiment_service=sentiment_service
        )

        await coordinator.initialize()
        yield coordinator
        await coordinator.shutdown()

    async def test_full_ooda_cycle(self, coordinator):
        result = await coordinator.run_cycle()

        assert result.observations is not None
        assert result.orientation is not None
        assert result.decision is not None
        assert result.execution_result is not None

        assert result.cycle_duration_ms < 1000

        assert result.observations.navagraha_state.timestamp is not None
        assert len(result.observations.navagraha_state.planets) == 9

    async def test_ooda_observe_phase(self, coordinator):
        observations = await coordinator._observe()

        assert observations.market_data is not None
        assert observations.navagraha_state is not None
        assert observations.sentiment is not None

        assert observations.navagraha_state.is_rahu_kala_active in [True, False]

    async def test_ooda_orient_phase(self, coordinator):
        observations = await coordinator._observe()
        orientation = await coordinator._orient(observations)

        assert orientation.guna_ratios is not None
        assert abs(sum([
            orientation.guna_ratios.sattva,
            orientation.guna_ratios.rajas,
            orientation.guna_ratios.tamas
        ]) - 1.0) < 0.01

        assert orientation.navagraha_snapshot_id is not None

    async def test_ooda_decide_phase_parallel_agents(self, coordinator):
        observations = await coordinator._observe()
        orientation = await coordinator._orient(observations)

        import time
        start = time.time()

        decision = await coordinator._decide(observations, orientation)

        elapsed = time.time() - start

        assert decision is not None
        assert elapsed < 0.5

        assert len(decision.agent_votes) == 5

    async def test_ooda_act_phase_paper_trading(self, coordinator):
        observations = await coordinator._observe()
        orientation = await coordinator._orient(observations)
        decision = await coordinator._decide(observations, orientation)

        execution_result = await coordinator._act(decision)

        assert execution_result.status in ['executed', 'rejected', 'pending']

        if execution_result.status == 'rejected':
            assert len(execution_result.rejection_reasons) > 0

    async def test_ooda_cycle_under_rahu_kala(self, coordinator, monkeypatch):
        async def mock_navagraha_state_rahu_kala():
            state = await coordinator.navagraha_service.get_current_state()
            state.is_rahu_kala_active = True
            return state

        monkeypatch.setattr(
            coordinator.navagraha_service,
            'get_current_state',
            mock_navagraha_state_rahu_kala
        )

        result = await coordinator.run_cycle()

        if result.decision.action == 'execute':
            assert result.execution_result.status == 'rejected'
            assert 'Rahu Kala' in str(result.execution_result.rejection_reasons)
```

### 3.2 Stress Testing OODA Loop

```python
@pytest.mark.stress
@pytest.mark.asyncio
class TestOODAStress:

    async def test_sustained_cycles(self, coordinator):
        results = []

        for i in range(100):
            result = await coordinator.run_cycle()
            results.append(result)
            await asyncio.sleep(0.1)

        cycle_times = [r.cycle_duration_ms for r in results]

        assert max(cycle_times) < 1500
        assert sum(cycle_times) / len(cycle_times) < 600

    async def test_concurrent_cycles(self, coordinator):
        tasks = [coordinator.run_cycle() for _ in range(10)]

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r.observations is not None for r in results)
```

---

## 4. Contract Testing for External APIs

### 4.1 CCXT Exchange Contract Tests

```python
import pytest
from backend.execution.ccxt_adapter import CCXTAdapter

@pytest.mark.contract
class TestCCXTContract:

    @pytest.fixture
    def exchange(self):
        return CCXTAdapter(exchange_id='binance', testnet=True)

    def test_fetch_balance_contract(self, exchange):
        balance = exchange.fetch_balance()

        assert isinstance(balance, dict)
        assert 'total' in balance
        assert 'free' in balance
        assert 'used' in balance

        if 'BTC' in balance['total']:
            assert isinstance(balance['total']['BTC'], (int, float))
            assert balance['total']['BTC'] >= 0

    def test_fetch_ticker_contract(self, exchange):
        ticker = exchange.fetch_ticker('BTC/USDT')

        required_fields = ['symbol', 'last', 'bid', 'ask', 'high', 'low', 'volume']
        for field in required_fields:
            assert field in ticker, f"Missing required field: {field}"

        assert ticker['last'] > 0
        assert ticker['bid'] < ticker['ask']

    def test_create_order_contract(self, exchange):
        order = exchange.create_order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.001,
            price=10000.0
        )

        required_fields = ['id', 'symbol', 'type', 'side', 'price', 'amount', 'status']
        for field in required_fields:
            assert field in order, f"Missing required field: {field}"

        assert order['status'] in ['open', 'closed', 'canceled', 'rejected']
```

### 4.2 Sentiment API Contract Tests

```python
@pytest.mark.contract
class TestSentimentAPIContract:

    @pytest.fixture
    def sentiment_client(self):
        return SentimentAPIClient()

    async def test_analyze_contract(self, sentiment_client):
        result = await sentiment_client.analyze("Bitcoin price surge")

        assert 'sentiment' in result
        assert 'score' in result
        assert result['sentiment'] in ['positive', 'negative', 'neutral']
        assert -1.0 <= result['score'] <= 1.0
```

---

## 5. Regression Detection

### 5.1 Performance Regression Tests

```python
@pytest.mark.regression
class TestPerformanceRegression:

    BASELINE_METRICS = {
        'ephemeris_calc_ms': 100,
        'cache_lookup_ms': 5,
        'ooda_cycle_ms': 500,
        'order_execution_ms': 300
    }

    def test_ephemeris_performance_regression(self):
        import time
        calculator = NavagrahaCalculator()

        times = []
        for _ in range(10):
            start = time.time()
            calculator.calculate(datetime.utcnow())
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        assert avg_time < self.BASELINE_METRICS['ephemeris_calc_ms'] * 1.2, \
            f"Performance regression: {avg_time:.2f}ms > baseline {self.BASELINE_METRICS['ephemeris_calc_ms']}ms"
```

---

## 6. Chaos Engineering Scenarios

### 6.1 Service Failure Scenarios

```python
@pytest.mark.chaos
@pytest.mark.asyncio
class TestChaosScenarios:

    async def test_redis_connection_loss(self, coordinator):
        await coordinator.cache_service.redis.close()

        result = await coordinator.run_cycle()

        assert result is not None
        assert result.observations is not None

    async def test_exchange_api_timeout(self, coordinator, monkeypatch):
        async def slow_api_call(*args, **kwargs):
            await asyncio.sleep(10)
            raise TimeoutError("API timeout")

        monkeypatch.setattr(
            coordinator.exchange_service,
            'fetch_ticker',
            slow_api_call
        )

        result = await coordinator.run_cycle()

        assert result.execution_result.status == 'rejected'
```

---

## 7. Test Coverage Targets

| Component | Unit | Integration | E2E | Target |
|-----------|------|-------------|-----|--------|
| NavagrahaCalculator | ✅ | ✅ | ✅ | 95% |
| GunaEngine | ✅ | ✅ | ✅ | 90% |
| OODACoordinator | ✅ | ✅ | ✅ | 85% |
| ElementalAgents | ✅ | ✅ | ✅ | 90% |
| KarmaFeedback | ✅ | ✅ | ❌ | 85% |
| ExecutionLayer | ✅ | ✅ | ✅ | 90% |
| MiFIDIIChecker | ✅ | ✅ | ✅ | 100% |

---

## Conclusion

This test strategy ensures:
✅ **Real ephemeris calculations** tested via invariants
✅ **Integration tests** validate component interactions
✅ **Contract tests** ensure external API compatibility
✅ **Regression tests** prevent performance degradation
✅ **Chaos tests** validate resilience
