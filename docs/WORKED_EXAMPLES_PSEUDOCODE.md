# Worked Examples & Pseudocode
## Samkhya Yoga Agentic Trader — Concrete Implementations

**Generated:** 2026-02-15
**Document Version:** 1.0
**Purpose:** Translate abstract philosophical concepts into executable code

---

## 1. Guna Modulation Logic

### Concept
Gunas (sattva/rajas/tamas) from Navagraha state modulate agent behavior:
- **Sattva** → Calm, cautious, reflective (reduce aggression)
- **Rajas** → Active, aggressive, dynamic (increase activity)
- **Tamas** → Inert, passive, minimal (reduce activity)

### Implementation

```python
from dataclasses import dataclass
from typing import Dict
from enum import Enum

class GunaType(str, Enum):
    SATTVA = "sattva"
    RAJAS = "rajas"
    TAMAS = "tamas"

@dataclass
class GunaRatios:
    sattva: float
    rajas: float
    tamas: float

    def __post_init__(self):
        total = self.sattva + self.rajas + self.tamas
        assert abs(total - 1.0) < 0.01, f"Gunas must sum to 1.0, got {total}"

    @property
    def dominant_guna(self) -> GunaType:
        if self.sattva >= self.rajas and self.sattva >= self.tamas:
            return GunaType.SATTVA
        elif self.rajas >= self.tamas:
            return GunaType.RAJAS
        else:
            return GunaType.TAMAS

class GunaModulator:
    MODULATION_PROFILES = {
        GunaType.SATTVA: {
            "confidence_multiplier": 0.8,
            "position_size_multiplier": 0.7,
            "holding_period_multiplier": 1.5,
            "risk_tolerance_multiplier": 0.6,
            "decision_delay_seconds": 30,
            "description": "Cautious, reflective, patient"
        },
        GunaType.RAJAS: {
            "confidence_multiplier": 1.2,
            "position_size_multiplier": 1.3,
            "holding_period_multiplier": 0.8,
            "risk_tolerance_multiplier": 1.4,
            "decision_delay_seconds": 5,
            "description": "Aggressive, dynamic, quick"
        },
        GunaType.TAMAS: {
            "confidence_multiplier": 0.5,
            "position_size_multiplier": 0.3,
            "holding_period_multiplier": 2.0,
            "risk_tolerance_multiplier": 0.3,
            "decision_delay_seconds": 60,
            "description": "Inert, minimal activity, passive"
        }
    }

    def modulate_trading_signal(
        self,
        signal: 'TradingSignal',
        guna_ratios: GunaRatios
    ) -> 'TradingSignal':
        dominant = guna_ratios.dominant_guna
        profile = self.MODULATION_PROFILES[dominant]

        modulated_signal = signal.copy()
        modulated_signal.confidence *= profile["confidence_multiplier"]
        modulated_signal.position_size *= profile["position_size_multiplier"]
        modulated_signal.holding_period_hours *= profile["holding_period_multiplier"]

        modulated_signal.confidence = min(1.0, max(0.0, modulated_signal.confidence))

        modulated_signal.metadata["guna_profile"] = profile["description"]
        modulated_signal.metadata["dominant_guna"] = dominant.value

        return modulated_signal

    def calculate_prana_decay_rate(self, guna_ratios: GunaRatios) -> float:
        return (
            guna_ratios.sattva * 0.01 +  # 1% per cycle (slow)
            guna_ratios.rajas * 0.03 +   # 3% per cycle (medium)
            guna_ratios.tamas * 0.07     # 7% per cycle (fast)
        )

class BaseElementalAgent:
    def __init__(self, element: str, navagraha_state: 'NavagrahaState'):
        self.element = element
        self.navagraha_state = navagraha_state
        self.prana = 100.0
        self.guna_modulator = GunaModulator()

    def observe(self, market_data: 'MarketData') -> 'Observation':
        self._update_prana()

        if self.prana < 20.0:
            return Observation(active=False, reason="low_prana")

        raw_signal = self._analyze_market(market_data)

        modulated_signal = self.guna_modulator.modulate_trading_signal(
            raw_signal,
            self.navagraha_state.guna_ratios
        )

        return Observation(
            signal=modulated_signal,
            prana_level=self.prana,
            guna_influence=self.navagraha_state.guna_ratios.dominant_guna
        )

    def _update_prana(self):
        decay_rate = self.guna_modulator.calculate_prana_decay_rate(
            self.navagraha_state.guna_ratios
        )
        self.prana = max(0.0, self.prana - decay_rate)

        if self.prana < 50.0:
            logger.warning(f"{self.element} agent prana low: {self.prana:.2f}")

    def _analyze_market(self, market_data: 'MarketData') -> 'TradingSignal':
        raise NotImplementedError("Subclass must implement")

@dataclass
class TradingSignal:
    symbol: str
    direction: str  # "long" or "short"
    confidence: float  # 0.0 to 1.0
    position_size: float  # Base size before modulation
    holding_period_hours: float
    metadata: Dict = None

    def copy(self):
        return TradingSignal(
            symbol=self.symbol,
            direction=self.direction,
            confidence=self.confidence,
            position_size=self.position_size,
            holding_period_hours=self.holding_period_hours,
            metadata=self.metadata.copy() if self.metadata else {}
        )
```

### Example Usage

```python
navagraha_state = NavagrahaState(
    guna_ratios=GunaRatios(sattva=0.6, rajas=0.3, tamas=0.1),
    ...
)

agent = FireElementAgent(element="fire", navagraha_state=navagraha_state)

raw_signal = TradingSignal(
    symbol="BTC/USDT",
    direction="long",
    confidence=0.8,
    position_size=1000.0,
    holding_period_hours=24.0
)

modulator = GunaModulator()
modulated_signal = modulator.modulate_trading_signal(raw_signal, navagraha_state.guna_ratios)

print(f"Original confidence: {raw_signal.confidence}")
print(f"Modulated confidence: {modulated_signal.confidence}")  # 0.64 (0.8 * 0.8)
print(f"Original position: {raw_signal.position_size}")
print(f"Modulated position: {modulated_signal.position_size}")  # 700.0 (1000 * 0.7)
print(f"Guna influence: {modulated_signal.metadata['dominant_guna']}")  # "sattva"
```

---

## 2. Karma Feedback Loop with Safety Bounds

### Concept
System learns from trade outcomes (karma) and adjusts parameters, but with strict safety bounds to prevent overfitting to lucky streaks.

### Implementation

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np
from scipy import stats

@dataclass
class TradeOutcome:
    trade_id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    pnl: float
    pnl_percent: float
    executed_at: datetime
    closed_at: datetime
    parameters_used: Dict[str, float]
    navagraha_state: 'NavagrahaState'

class KarmaLearner:
    SAFETY_BOUNDS = {
        "max_parameter_shift_percent": 0.20,  # 20% max change per review
        "min_sample_size": 30,  # Minimum trades before adjustment
        "significance_threshold": 0.05,  # p-value < 0.05
        "max_sharpe_ratio": 3.0,  # Suspicious if > 3.0
        "lookback_window_days": 30,  # Only recent history
        "parameter_bounds": {
            "risk_tolerance": (0.01, 0.10),  # 1% to 10%
            "position_size_base": (100.0, 10000.0),
            "confidence_threshold": (0.5, 0.9),
            "holding_period_hours": (1.0, 168.0)  # 1 hour to 1 week
        }
    }

    def __init__(self):
        self.outcome_history: List[TradeOutcome] = []
        self.parameter_history: List[Dict[str, float]] = []
        self.adjustment_log: List[Dict] = []

    def record_outcome(self, outcome: TradeOutcome):
        self.outcome_history.append(outcome)

        cutoff_date = datetime.utcnow() - timedelta(
            days=self.SAFETY_BOUNDS["lookback_window_days"]
        )
        self.outcome_history = [
            o for o in self.outcome_history
            if o.executed_at >= cutoff_date
        ]

    def should_adjust_parameters(self) -> bool:
        if len(self.outcome_history) < self.SAFETY_BOUNDS["min_sample_size"]:
            logger.info(
                f"Insufficient samples: {len(self.outcome_history)}/{self.SAFETY_BOUNDS['min_sample_size']}"
            )
            return False

        recent_sharpe = self._calculate_sharpe_ratio(self.outcome_history[-30:])
        if recent_sharpe > self.SAFETY_BOUNDS["max_sharpe_ratio"]:
            logger.warning(
                f"Sharpe ratio suspiciously high: {recent_sharpe:.2f}, possible overfitting"
            )
            return False

        return True

    def adjust_parameters(
        self,
        current_params: Dict[str, float]
    ) -> Dict[str, float]:
        if not self.should_adjust_parameters():
            return current_params

        recent_outcomes = self.outcome_history[-30:]

        win_rate = sum(1 for o in recent_outcomes if o.pnl > 0) / len(recent_outcomes)
        avg_pnl_percent = np.mean([o.pnl_percent for o in recent_outcomes])
        sharpe_ratio = self._calculate_sharpe_ratio(recent_outcomes)

        if not self._is_statistically_significant(recent_outcomes):
            logger.info("Results not statistically significant, no adjustment")
            return current_params

        adjustment_direction = self._determine_adjustment_direction(
            win_rate, avg_pnl_percent, sharpe_ratio
        )

        new_params = current_params.copy()

        for param_name, current_value in current_params.items():
            if param_name not in self.SAFETY_BOUNDS["parameter_bounds"]:
                continue

            adjustment_factor = self._calculate_adjustment_factor(
                param_name, adjustment_direction, win_rate
            )

            proposed_value = current_value * (1 + adjustment_factor)

            min_bound, max_bound = self.SAFETY_BOUNDS["parameter_bounds"][param_name]

            max_shift = current_value * self.SAFETY_BOUNDS["max_parameter_shift_percent"]
            proposed_value = min(proposed_value, current_value + max_shift)
            proposed_value = max(proposed_value, current_value - max_shift)

            new_params[param_name] = np.clip(proposed_value, min_bound, max_bound)

        self._log_adjustment(current_params, new_params, win_rate, avg_pnl_percent, sharpe_ratio)

        return new_params

    def _calculate_sharpe_ratio(self, outcomes: List[TradeOutcome]) -> float:
        if not outcomes:
            return 0.0

        returns = [o.pnl_percent for o in outcomes]
        if len(returns) < 2:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)

        if std_return == 0:
            return 0.0

        return mean_return / std_return * np.sqrt(252)  # Annualized

    def _is_statistically_significant(self, outcomes: List[TradeOutcome]) -> bool:
        returns = [o.pnl_percent for o in outcomes]

        t_stat, p_value = stats.ttest_1samp(returns, 0)

        is_significant = p_value < self.SAFETY_BOUNDS["significance_threshold"]

        logger.info(f"Statistical test: t={t_stat:.2f}, p={p_value:.4f}, significant={is_significant}")

        return is_significant

    def _determine_adjustment_direction(
        self,
        win_rate: float,
        avg_pnl: float,
        sharpe: float
    ) -> str:
        if win_rate > 0.6 and avg_pnl > 0.02 and sharpe > 1.0:
            return "increase_aggression"
        elif win_rate < 0.4 or avg_pnl < -0.01:
            return "decrease_aggression"
        else:
            return "neutral"

    def _calculate_adjustment_factor(
        self,
        param_name: str,
        direction: str,
        win_rate: float
    ) -> float:
        if direction == "neutral":
            return 0.0

        base_adjustment = 0.10  # 10% base adjustment

        if direction == "increase_aggression":
            if param_name == "risk_tolerance":
                return base_adjustment
            elif param_name == "position_size_base":
                return base_adjustment
            elif param_name == "confidence_threshold":
                return -base_adjustment  # Lower threshold = more trades
        else:  # decrease_aggression
            if param_name == "risk_tolerance":
                return -base_adjustment
            elif param_name == "position_size_base":
                return -base_adjustment
            elif param_name == "confidence_threshold":
                return base_adjustment  # Higher threshold = fewer trades

        return 0.0

    def _log_adjustment(
        self,
        old_params: Dict[str, float],
        new_params: Dict[str, float],
        win_rate: float,
        avg_pnl: float,
        sharpe: float
    ):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "old_params": old_params,
            "new_params": new_params,
            "performance": {
                "win_rate": win_rate,
                "avg_pnl_percent": avg_pnl,
                "sharpe_ratio": sharpe,
                "sample_size": len(self.outcome_history)
            },
            "parameter_shifts": {
                param: ((new_params[param] - old_params[param]) / old_params[param] * 100)
                for param in old_params.keys()
                if param in new_params
            }
        }

        self.adjustment_log.append(log_entry)
        logger.info(f"Karma adjustment: {log_entry}")
```

### Example Usage

```python
learner = KarmaLearner()

for outcome in trade_outcomes:
    learner.record_outcome(outcome)

if learner.should_adjust_parameters():
    current_params = {
        "risk_tolerance": 0.05,
        "position_size_base": 1000.0,
        "confidence_threshold": 0.7,
        "holding_period_hours": 24.0
    }

    new_params = learner.adjust_parameters(current_params)

    print("Parameter Adjustments:")
    for param, old_val in current_params.items():
        new_val = new_params[param]
        shift_pct = (new_val - old_val) / old_val * 100
        print(f"  {param}: {old_val:.4f} → {new_val:.4f} ({shift_pct:+.2f}%)")
```

---

## 3. MiFID II Pre-Trade Check Logic

### Concept
European MiFID II regulations require pre-trade compliance checks before order execution, including position limits, best execution obligations, and client classification.

### Implementation

```python
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from datetime import datetime

class ClientClassification(str, Enum):
    RETAIL = "retail"
    PROFESSIONAL = "professional"
    ELIGIBLE_COUNTERPARTY = "eligible_counterparty"

class RejectionReason(str, Enum):
    POSITION_LIMIT_EXCEEDED = "position_limit_exceeded"
    CONCENTRATION_RISK = "concentration_risk"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    RESTRICTED_INSTRUMENT = "restricted_instrument"
    CLIENT_NOT_AUTHORIZED = "client_not_authorized"
    BEST_EXECUTION_UNAVAILABLE = "best_execution_unavailable"

@dataclass
class PreTradeCheckResult:
    approved: bool
    rejection_reason: Optional[RejectionReason]
    rejection_details: Optional[str]
    warnings: List[str]
    audit_trail_id: str
    checked_at: datetime

@dataclass
class Order:
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    price: Optional[float]
    order_type: str  # "market" or "limit"
    client_id: str
    portfolio_id: str

@dataclass
class MiFIDLimits:
    max_position_size_per_instrument: float = 100000.0  # USD
    max_portfolio_concentration: float = 0.30  # 30%
    max_daily_turnover: float = 500000.0  # USD
    restricted_instruments: List[str] = None

class MiFIDPreTradeChecker:
    def __init__(
        self,
        limits: MiFIDLimits,
        database: 'Database',
        audit_logger: 'AuditLogger'
    ):
        self.limits = limits
        self.db = database
        self.audit = audit_logger

    def check(self, order: Order) -> PreTradeCheckResult:
        audit_trail_id = self._generate_audit_id()
        warnings = []

        client = self.db.get_client(order.client_id)
        if not client:
            return self._reject(
                RejectionReason.CLIENT_NOT_AUTHORIZED,
                f"Client {order.client_id} not found",
                audit_trail_id
            )

        if self._is_instrument_restricted(order.symbol):
            return self._reject(
                RejectionReason.RESTRICTED_INSTRUMENT,
                f"Instrument {order.symbol} is restricted for trading",
                audit_trail_id
            )

        current_position = self.db.get_position(order.portfolio_id, order.symbol)
        projected_position = self._calculate_projected_position(order, current_position)

        if abs(projected_position.value_usd) > self.limits.max_position_size_per_instrument:
            return self._reject(
                RejectionReason.POSITION_LIMIT_EXCEEDED,
                f"Position limit: {projected_position.value_usd:.2f} > {self.limits.max_position_size_per_instrument}",
                audit_trail_id
            )

        portfolio = self.db.get_portfolio(order.portfolio_id)
        projected_concentration = self._calculate_concentration(portfolio, order)

        if projected_concentration > self.limits.max_portfolio_concentration:
            return self._reject(
                RejectionReason.CONCENTRATION_RISK,
                f"Concentration risk: {projected_concentration:.1%} > {self.limits.max_portfolio_concentration:.1%}",
                audit_trail_id
            )

        daily_turnover = self.db.get_daily_turnover(order.portfolio_id, datetime.utcnow().date())
        order_value = self._estimate_order_value(order)

        if daily_turnover + order_value > self.limits.max_daily_turnover:
            return self._reject(
                RejectionReason.INSUFFICIENT_FUNDS,
                f"Daily turnover limit exceeded: {daily_turnover + order_value:.2f} > {self.limits.max_daily_turnover}",
                audit_trail_id
            )

        if client.classification == ClientClassification.RETAIL:
            warnings.append("Retail client: additional protections apply")

        if projected_concentration > 0.20:
            warnings.append(f"High concentration in {order.symbol}: {projected_concentration:.1%}")

        self.audit.log_pretrade_check(
            audit_trail_id=audit_trail_id,
            order=order,
            client=client,
            result="APPROVED",
            warnings=warnings
        )

        return PreTradeCheckResult(
            approved=True,
            rejection_reason=None,
            rejection_details=None,
            warnings=warnings,
            audit_trail_id=audit_trail_id,
            checked_at=datetime.utcnow()
        )

    def _reject(
        self,
        reason: RejectionReason,
        details: str,
        audit_trail_id: str
    ) -> PreTradeCheckResult:
        self.audit.log_pretrade_check(
            audit_trail_id=audit_trail_id,
            result="REJECTED",
            reason=reason.value,
            details=details
        )

        return PreTradeCheckResult(
            approved=False,
            rejection_reason=reason,
            rejection_details=details,
            warnings=[],
            audit_trail_id=audit_trail_id,
            checked_at=datetime.utcnow()
        )

    def _is_instrument_restricted(self, symbol: str) -> bool:
        if not self.limits.restricted_instruments:
            return False
        return symbol in self.limits.restricted_instruments

    def _calculate_projected_position(self, order: Order, current_position: Optional['Position']) -> 'ProjectedPosition':
        current_qty = current_position.quantity if current_position else 0.0

        if order.side == "buy":
            projected_qty = current_qty + order.quantity
        else:  # sell
            projected_qty = current_qty - order.quantity

        current_price = order.price or self._get_market_price(order.symbol)
        value_usd = projected_qty * current_price

        return ProjectedPosition(quantity=projected_qty, value_usd=value_usd)

    def _calculate_concentration(self, portfolio: 'Portfolio', order: Order) -> float:
        order_value = self._estimate_order_value(order)
        total_portfolio_value = portfolio.total_value_usd

        if total_portfolio_value == 0:
            return 0.0

        current_instrument_value = portfolio.positions.get(order.symbol, 0.0)
        projected_instrument_value = current_instrument_value + order_value

        return projected_instrument_value / total_portfolio_value

    def _estimate_order_value(self, order: Order) -> float:
        price = order.price or self._get_market_price(order.symbol)
        return order.quantity * price

    def _get_market_price(self, symbol: str) -> float:
        ticker = self.db.get_latest_ticker(symbol)
        return ticker.last if ticker else 0.0

    def _generate_audit_id(self) -> str:
        return f"mifid2-check-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

@dataclass
class ProjectedPosition:
    quantity: float
    value_usd: float
```

### Example Usage

```python
limits = MiFIDLimits(
    max_position_size_per_instrument=100000.0,
    max_portfolio_concentration=0.30,
    max_daily_turnover=500000.0,
    restricted_instruments=["LUNA/USD"]  # After Terra collapse
)

checker = MiFIDPreTradeChecker(limits, database, audit_logger)

order = Order(
    symbol="BTC/USDT",
    side="buy",
    quantity=2.5,
    price=50000.0,
    order_type="limit",
    client_id="client-123",
    portfolio_id="portfolio-456"
)

result = checker.check(order)

if result.approved:
    print(f"Order approved: {result.audit_trail_id}")
    if result.warnings:
        print(f"Warnings: {', '.join(result.warnings)}")
    execute_order(order)
else:
    print(f"Order rejected: {result.rejection_reason.value}")
    print(f"Details: {result.rejection_details}")
    notify_client(order.client_id, result)
```

---

*End of Worked Examples & Pseudocode Document*
