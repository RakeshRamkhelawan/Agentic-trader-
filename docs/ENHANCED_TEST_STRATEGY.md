# Enhanced Test Strategy
## Samkhya Yoga Agentic Trader — Comprehensive Testing Approach

**Generated:** 2026-02-15  
**Document Version:** 1.0  
**Test Philosophy:** Real ephemeris, no mocks for critical paths, invariant-driven validation

---

## Executive Summary

This test strategy ensures production-grade reliability while preserving the philosophical coherence of the Samkhya Yoga trading system. Key principles:

1. **No Mocking for Critical Paths:** Real Swiss Ephemeris calculations in all tests
2. **Invariant Testing:** Enforce cosmic/physical constraints (9 planets, Rahu retrograde, etc.)
3. **Contract Testing:** Validate external API schemas (CCXT, sentiment APIs)
4. **Integration Testing:** Full OODA loop with real Navagraha state
5. **Performance Regression:** Automated latency budget enforcement
6. **Chaos Engineering:** Failure scenario testing

**Coverage Targets:**
- Unit Tests: >80% code coverage
- Integration Tests: All OODA paths covered
- Contract Tests: 100% external API coverage
- E2E Tests: Critical user journeys (trade lifecycle)

---

## 1. Unit Testing Strategy

### 1.1 Ephemeris Invariant Testing (No Mocks)

**Philosophy:** Swiss Ephemeris calculations must use real astronomical data, never mocks. Validate cosmic invariants.

```python
import pytest
from datetime import datetime
from backend.core.navagraha.ephemeris import EphemerisCalculator
from backend.core.navagraha.models import PlanetName, Location

class TestEphemerisInvariants:
    @pytest.fixture
    def calculator(self):
        return EphemerisCalculator()
    
    @pytest.fixture
    def test_location(self):
        return Location(latitude=28.6139, longitude=77.2090, name="Delhi")
    
    def test_exactly_nine_planets_returned(self, calculator, test_location):
        """Invariant: Always return exactly 9 Navagraha planets."""
        dt = datetime(2026, 2, 15, 12, 0, 0)
        result = calculator.calculate(dt, test_location)
        
        assert len(result.planets) == 9, "Must return exactly 9 planets"
        
        expected_planets = {
            PlanetName.SUN, PlanetName.MOON, PlanetName.MARS,
            PlanetName.MERCURY, PlanetName.JUPITER, PlanetName.VENUS,
            PlanetName.SATURN, PlanetName.RAHU, PlanetName.KETU
        }
        actual_planets = {p.name for p in result.planets}
        assert actual_planets == expected_planets
    
    def test_rahu_always_retrograde(self, calculator, test_location):
        """Invariant: Rahu (North Node) is always retrograde by definition."""
        dt = datetime(2026, 2, 15, 12, 0, 0)
        result = calculator.calculate(dt, test_location)
        
        rahu = next(p for p in result.planets if p.name == PlanetName.RAHU)
        assert rahu.is_retrograde is True, "Rahu must always be retrograde"
    
    def test_ketu_always_retrograde(self, calculator, test_location):
        """Invariant: Ketu (South Node) is always retrograde by definition."""
        dt = datetime(2026, 2, 15, 12, 0, 0)
        result = calculator.calculate(dt, test_location)
        
        ketu = next(p for p in result.planets if p.name == PlanetName.KETU)
        assert ketu.is_retrograde is True, "Ketu must always be retrograde"
    
    def test_rahu_ketu_opposite_positions(self, calculator, test_location):
        """Invariant: Rahu and Ketu are always 180 degrees apart."""
        dt = datetime(2026, 2, 15, 12, 0, 0)
        result = calculator.calculate(dt, test_location)
        
        rahu = next(p for p in result.planets if p.name == PlanetName.RAHU)
        ketu = next(p for p in result.planets if p.name == PlanetName.KETU)
        
        diff = abs(rahu.longitude - ketu.longitude)
        diff_normalized = min(diff, 360 - diff)
        
        assert abs(diff_normalized - 180.0) < 1.0, f"Rahu-Ketu must be ~180° apart, got {diff_normalized:.2f}"
    
    def test_longitude_valid_range(self, calculator, test_location):
        """Invariant: All longitudes must be in [0, 360) degrees."""
        dt = datetime(2026, 2, 15, 12, 0, 0)
        result = calculator.calculate(dt, test_location)
        
        for planet in result.planets:
            assert 0 <= planet.longitude < 360, \
                f"{planet.name} longitude {planet.longitude} out of range [0, 360)"
    
    def test_latitude_valid_range(self, calculator, test_location):
        """Invariant: All latitudes must be in [-90, 90] degrees."""
        dt = datetime(2026, 2, 15, 12, 0, 0)
        result = calculator.calculate(dt, test_location)
        
        for planet in result.planets:
            assert -90 <= planet.latitude <= 90, \
                f"{planet.name} latitude {planet.latitude} out of range [-90, 90]"
    
    @pytest.mark.parametrize("date_str", [
        "2026-01-01 00:00:00",
        "2026-06-15 12:30:00",
        "2026-12-31 23:59:59",
    ])
    def test_calculation_consistency_across_year(self, calculator, test_location, date_str):
        """Test that calculations work consistently throughout the year."""
        dt = datetime.fromisoformat(date_str)
        result = calculator.calculate(dt, test_location)
        
        assert len(result.planets) == 9
        assert all(p.longitude is not None for p in result.planets)
    
    def test_calculation_repeatability(self, calculator, test_location):
        """Test that same input produces same output (deterministic)."""
        dt = datetime(2026, 2, 15, 12, 0, 0)
        
        result1 = calculator.calculate(dt, test_location)
        result2 = calculator.calculate(dt, test_location)
        
        for p1, p2 in zip(result1.planets, result2.planets):
            assert p1.name == p2.name
            assert abs(p1.longitude - p2.longitude) < 0.001, "Calculations must be deterministic"
    
    def test_sun_moves_approximately_one_degree_per_day(self, calculator, test_location):
        """Sanity check: Sun moves ~1° per day."""
        dt1 = datetime(2026, 2, 15, 12, 0, 0)
        dt2 = datetime(2026, 2, 16, 12, 0, 0)
        
        result1 = calculator.calculate(dt1, test_location)
        result2 = calculator.calculate(dt2, test_location)
        
        sun1 = next(p for p in result1.planets if p.name == PlanetName.SUN)
        sun2 = next(p for p in result2.planets if p.name == PlanetName.SUN)
        
        diff = abs(sun2.longitude - sun1.longitude)
        assert 0.9 < diff < 1.1, f"Sun should move ~1° per day, got {diff:.2f}°"
```

### 1.2 Guna Modulation Testing

```python
class TestGunaModulation:
    def test_sattva_reduces_aggression(self):
        """Sattvic dominance should reduce position size and confidence."""
        guna_ratios = GunaRatios(sattva=0.7, rajas=0.2, tamas=0.1)
        modulator = GunaModulator()
        
        signal = TradingSignal(
            symbol="BTC/USDT",
            direction="long",
            confidence=0.8,
            position_size=1000.0,
            holding_period_hours=24.0
        )
        
        modulated = modulator.modulate_trading_signal(signal, guna_ratios)
        
        assert modulated.confidence < signal.confidence
        assert modulated.position_size < signal.position_size
        assert modulated.holding_period_hours > signal.holding_period_hours
    
    def test_rajas_increases_aggression(self):
        """Rajasic dominance should increase position size and confidence."""
        guna_ratios = GunaRatios(sattva=0.2, rajas=0.7, tamas=0.1)
        modulator = GunaModulator()
        
        signal = TradingSignal(
            symbol="BTC/USDT",
            direction="long",
            confidence=0.8,
            position_size=1000.0,
            holding_period_hours=24.0
        )
        
        modulated = modulator.modulate_trading_signal(signal, guna_ratios)
        
        assert modulated.confidence > signal.confidence
        assert modulated.position_size > signal.position_size
        assert modulated.holding_period_hours < signal.holding_period_hours
    
    def test_tamas_minimizes_activity(self):
        """Tamasic dominance should drastically reduce activity."""
        guna_ratios = GunaRatios(sattva=0.1, rajas=0.1, tamas=0.8)
        modulator = GunaModulator()
        
        signal = TradingSignal(
            symbol="BTC/USDT",
            direction="long",
            confidence=0.8,
            position_size=1000.0,
            holding_period_hours=24.0
        )
        
        modulated = modulator.modulate_trading_signal(signal, guna_ratios)
        
        assert modulated.confidence < 0.5  # Very low confidence
        assert modulated.position_size < 500.0  # Very small position
    
    def test_prana_decay_rate_varies_by_guna(self):
        """Prana decay should be fastest with tamas, slowest with sattva."""
        modulator = GunaModulator()
        
        sattva_decay = modulator.calculate_prana_decay_rate(
            GunaRatios(sattva=0.9, rajas=0.05, tamas=0.05)
        )
        rajas_decay = modulator.calculate_prana_decay_rate(
            GunaRatios(sattva=0.05, rajas=0.9, tamas=0.05)
        )
        tamas_decay = modulator.calculate_prana_decay_rate(
            GunaRatios(sattva=0.05, rajas=0.05, tamas=0.9)
        )
        
        assert sattva_decay < rajas_decay < tamas_decay
```

### 1.3 Karma Learning Safety Bounds Testing

```python
class TestKarmaLearnerSafetyBounds:
    def test_parameter_shift_never_exceeds_20_percent(self):
        """Karma learning must never shift parameters > 20% per review."""
        learner = KarmaLearner()
        
        # Simulate 50 winning trades (best case scenario)
        for i in range(50):
            outcome = TradeOutcome(
                trade_id=f"trade-{i}",
                pnl=100.0,
                pnl_percent=0.05,
                executed_at=datetime.utcnow(),
                closed_at=datetime.utcnow(),
                parameters_used={},
                navagraha_state=None
            )
            learner.record_outcome(outcome)
        
        old_params = {"risk_tolerance": 0.05}
        new_params = learner.adjust_parameters(old_params)
        
        shift = abs(new_params["risk_tolerance"] - old_params["risk_tolerance"])
        max_shift = old_params["risk_tolerance"] * 0.20
        
        assert shift <= max_shift, f"Parameter shift {shift:.4f} exceeds max {max_shift:.4f}"
    
    def test_insufficient_sample_size_prevents_adjustment(self):
        """Must have minimum 30 trades before adjusting parameters."""
        learner = KarmaLearner()
        
        for i in range(20):  # Only 20 trades
            outcome = TradeOutcome(
                trade_id=f"trade-{i}",
                pnl=50.0,
                pnl_percent=0.03,
                executed_at=datetime.utcnow(),
                closed_at=datetime.utcnow(),
                parameters_used={},
                navagraha_state=None
            )
            learner.record_outcome(outcome)
        
        assert learner.should_adjust_parameters() is False
    
    def test_suspiciously_high_sharpe_prevents_adjustment(self):
        """Sharpe ratio > 3.0 indicates possible overfitting, prevent adjustment."""
        learner = KarmaLearner()
        
        # Simulate unrealistically consistent wins
        for i in range(50):
            outcome = TradeOutcome(
                trade_id=f"trade-{i}",
                pnl=100.0,
                pnl_percent=0.10,  # 10% every trade (unrealistic)
                executed_at=datetime.utcnow(),
                closed_at=datetime.utcnow(),
                parameters_used={},
                navagraha_state=None
            )
            learner.record_outcome(outcome)
        
        assert learner.should_adjust_parameters() is False, "Should detect overfitting"
    
    def test_parameters_stay_within_absolute_bounds(self):
        """Parameters must never exceed absolute min/max bounds."""
        learner = KarmaLearner()
        
        for i in range(50):
            outcome = TradeOutcome(
                trade_id=f"trade-{i}",
                pnl=1000.0,
                pnl_percent=0.20,
                executed_at=datetime.utcnow(),
                closed_at=datetime.utcnow(),
                parameters_used={},
                navagraha_state=None
            )
            learner.record_outcome(outcome)
        
        old_params = {"risk_tolerance": 0.09}  # Near upper bound
        new_params = learner.adjust_parameters(old_params)
        
        assert new_params["risk_tolerance"] <= 0.10, "Must respect absolute upper bound"
        assert new_params["risk_tolerance"] >= 0.01, "Must respect absolute lower bound"
```

---

## 2. Integration Testing Strategy

### 2.1 Full OODA Loop Integration

```python
class TestOODALoopIntegration:
    @pytest.fixture
    def ooda_coordinator(self):
        return OODACoordinator(
            navagraha_calculator=EphemerisCalculator(),
            market_data_service=MarketDataService(),
            strategy_selector=StrategySelector(),
            risk_assessor=RiskAssessor(),
            order_executor=OrderExecutor()
        )
    
    def test_full_ooda_cycle_with_real_ephemeris(self, ooda_coordinator):
        """Integration test: Full OODA cycle with real Navagraha state."""
        result = ooda_coordinator.run_cycle(
            datetime.utcnow(),
            Location(latitude=28.6, longitude=77.2)
        )
        
        # Validate state threading
        assert result.context.navagraha_state is not None
        assert len(result.context.navagraha_state.planets) == 9
        
        # Validate OODA phases executed
        assert result.observation is not None
        assert result.orientation is not None
        assert result.decision is not None
        
        # Validate Navagraha influence
        assert result.metadata["dasha_influenced_strategy"] is True
        assert result.metadata["guna_modulated_risk"] is True
    
    def test_rahu_kala_blocks_execution(self, ooda_coordinator, monkeypatch):
        """Test that Rahu Kala gate prevents order execution."""
        # Mock Rahu Kala to be active
        def mock_is_rahu_kala(navagraha_state):
            return True
        
        monkeypatch.setattr(
            "backend.orchestration.ooda_coordinator.is_rahu_kala_active",
            mock_is_rahu_kala
        )
        
        result = ooda_coordinator.run_cycle(
            datetime.utcnow(),
            Location(latitude=28.6, longitude=77.2)
        )
        
        assert result.execution_result.status == "BLOCKED"
        assert "rahu_kala" in result.execution_result.reason.lower()
    
    def test_dasha_influences_strategy_selection(self, ooda_coordinator):
        """Test that Dasha period influences strategy selection."""
        result = ooda_coordinator.run_cycle(
            datetime.utcnow(),
            Location(latitude=28.6, longitude=77.2)
        )
        
        dasha = result.context.navagraha_state.current_dasha.planet
        strategy_name = result.orientation.selected_strategy.name
        
        # Verify strategy selection matches Dasha → Strategy mapping
        expected_strategy_type = DASHA_STRATEGY_MAP.get(dasha)
        assert expected_strategy_type in strategy_name
```

### 2.2 Agent Coordination Integration

```python
class TestAgentCoordination:
    def test_all_five_elements_participate(self):
        """Test that all 5 elemental agents contribute to decision."""
        coordinator = ElementalOrchestrator()
        navagraha_state = NavagrahaState(...)
        market_data = MarketData(...)
        
        result = coordinator.coordinate_agents(navagraha_state, market_data)
        
        assert "ether" in result.agent_contributions
        assert "air" in result.agent_contributions
        assert "fire" in result.agent_contributions
        assert "water" in result.agent_contributions
        assert "earth" in result.agent_contributions
    
    def test_low_prana_agents_excluded(self):
        """Agents with prana < 20 should not participate."""
        # Test implementation...
        pass
```

---

## 3. Contract Testing for External APIs

### 3.1 CCXT Exchange Contract Tests

```python
import ccxt
import pytest

class TestCCXTContracts:
    """Contract tests ensure exchange APIs match expected schema."""
    
    @pytest.mark.integration
    @pytest.mark.parametrize("exchange_id", [
        "binance", "coinbase", "kraken", "bybit", "okx"
    ])
    def test_fetch_ticker_contract(self, exchange_id):
        """Validate ticker response schema for each exchange."""
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class()
        
        ticker = exchange.fetch_ticker("BTC/USDT")
        
        # Required fields per CCXT unified API
        assert "symbol" in ticker
        assert "last" in ticker
        assert "bid" in ticker
        assert "ask" in ticker
        assert "high" in ticker
        assert "low" in ticker
        assert "volume" in ticker
        assert "timestamp" in ticker
        
        # Type validation
        assert isinstance(ticker["last"], (int, float))
        assert ticker["last"] > 0
        assert isinstance(ticker["bid"], (int, float))
        assert isinstance(ticker["ask"], (int, float))
        assert ticker["bid"] < ticker["ask"], "Bid must be less than ask"
    
    @pytest.mark.integration
    def test_fetch_order_book_contract(self):
        """Validate order book response schema."""
        exchange = ccxt.binance()
        order_book = exchange.fetch_order_book("BTC/USDT")
        
        assert "bids" in order_book
        assert "asks" in order_book
        assert "timestamp" in order_book
        
        # Validate structure
        assert len(order_book["bids"]) > 0
        assert len(order_book["asks"]) > 0
        
        # Each entry should be [price, amount]
        first_bid = order_book["bids"][0]
        assert len(first_bid) == 2
        assert isinstance(first_bid[0], (int, float))  # price
        assert isinstance(first_bid[1], (int, float))  # amount
```

### 3.2 Sentiment API Contract Tests

```python
class TestSentimentAPIContracts:
    @pytest.mark.integration
    def test_news_api_contract(self):
        """Validate news sentiment API response schema."""
        client = NewsAPIClient()
        response = client.get_crypto_news("bitcoin")
        
        assert "articles" in response
        assert isinstance(response["articles"], list)
        
        if len(response["articles"]) > 0:
            article = response["articles"][0]
            assert "title" in article
            assert "sentiment_score" in article
            assert -1.0 <= article["sentiment_score"] <= 1.0
```

---

## 4. Performance Regression Testing

### 4.1 Latency Budget Enforcement

```python
import time
import pytest

class TestPerformanceRegression:
    def test_ephemeris_calculation_cold_cache_under_500ms(self):
        """Ephemeris calculation must complete in <500ms (cold cache)."""
        calculator = EphemerisCalculator()
        
        start = time.time()
        result = calculator.calculate(
            datetime.utcnow(),
            Location(latitude=28.6, longitude=77.2)
        )
        elapsed_ms = (time.time() - start) * 1000
        
        assert elapsed_ms < 500, f"Ephemeris calc took {elapsed_ms:.2f}ms, expected <500ms"
    
    def test_ephemeris_calculation_warm_cache_under_50ms(self):
        """Cached ephemeris retrieval must complete in <50ms."""
        calculator = EphemerisCalculator()
        dt = datetime.utcnow()
        location = Location(latitude=28.6, longitude=77.2)
        
        # Warm cache
        calculator.calculate_with_cache(dt, location)
        
        # Test cached retrieval
        start = time.time()
        result = calculator.calculate_with_cache(dt, location)
        elapsed_ms = (time.time() - start) * 1000
        
        assert elapsed_ms < 50, f"Cached retrieval took {elapsed_ms:.2f}ms, expected <50ms"
    
    def test_full_ooda_cycle_under_2_seconds(self):
        """Full OODA cycle must complete in <2 seconds."""
        coordinator = OODACoordinator()
        
        start = time.time()
        result = coordinator.run_cycle(
            datetime.utcnow(),
            Location(latitude=28.6, longitude=77.2)
        )
        elapsed = time.time() - start
        
        assert elapsed < 2.0, f"OODA cycle took {elapsed:.2f}s, expected <2s"
```

---

## 5. Chaos Engineering Tests

### 5.1 Service Failure Scenarios

```python
class TestChaosEngineering:
    def test_exchange_api_timeout_triggers_circuit_breaker(self, monkeypatch):
        """Test circuit breaker opens on repeated timeouts."""
        def mock_timeout(*args, **kwargs):
            raise ccxt.RequestTimeout("Simulated timeout")
        
        monkeypatch.setattr(ccxt.binance, "fetch_ticker", mock_timeout)
        
        breaker = CircuitBreaker("binance", config=CircuitBreakerConfig(
            failure_threshold=3,
            timeout_seconds=30
        ))
        
        # Trigger 3 failures
        for i in range(3):
            with pytest.raises(ccxt.RequestTimeout):
                breaker.call(ccxt.binance().fetch_ticker, "BTC/USDT")
        
        # Circuit should now be OPEN
        assert breaker._get_state() == CircuitState.OPEN
        
        # Next call should fail fast
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(ccxt.binance().fetch_ticker, "BTC/USDT")
    
    def test_ephemeris_failure_uses_last_known_state(self, monkeypatch):
        """Test graceful degradation when ephemeris calculation fails."""
        calculator = NavagrahaStateCalculator()
        
        # Store a known good state
        good_state = calculator.calculate(datetime.utcnow(), Location(...))
        
        # Simulate ephemeris failure
        def mock_failure(*args, **kwargs):
            raise EphemerisCalculationError("Simulated failure")
        
        monkeypatch.setattr(calculator, "_calculate_real", mock_failure)
        
        # Should fallback to last known state
        fallback_state = calculator.calculate_with_fallback(datetime.utcnow(), Location(...))
        
        assert fallback_state is not None
        assert fallback_state.is_fallback is True
```

---

## 6. Test Execution & CI/CD Integration

### 6.1 Test Pyramid

```
```
                  /\
                 /  \
                /E2E \     (5% - 10 tests)
               /______\
              /        \
             /Integration\   (15% - 50 tests)
            /____________\
           /              \
          /   Unit Tests   \  (80% - 300+ tests)
         /__________________\
```
```

### 6.2 CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install Swiss Ephemeris files
        run: |
          mkdir -p /usr/share/ephe
          # Download DE431 files from NASA JPL
      - name: Run Unit Tests
        run: pytest tests/unit/ -v --cov=backend --cov-report=xml
      - name: Upload Coverage
        uses: codecov/codecov-action@v2
  
  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
      postgres:
        image: postgres:15
    steps:
      - name: Run Integration Tests
        run: pytest tests/integration/ -v --maxfail=3
  
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run CCXT Contract Tests
        run: pytest tests/contract/ -v -m contract
```

---

*End of Enhanced Test Strategy Document*