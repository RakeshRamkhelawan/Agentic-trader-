# 📋 MASTERPROMPT VOOR CODE AGENT (V17 IMPLEMENTATIE)

**Rol & Context:**
Je bent de lead developer van het Elemental Trading Systeem. We gaan van V16 naar V17. Het VedAstro systeem (10/10 E2E tests geslaagd) is nu productie-ready en moet geïntegreerd worden in de backtest engine.

**Doel:**
Creëer een hybride systeem dat:
1. VedAstro TradingSignalGenerator gebruikt als primaire entry driver
2. Elemental agents behoudt voor risk management (Fire=position sizing, Earth=entry blocking)
3. Consensus rate verhoogt van 9% naar 40-60%
4. Execute rate verdubbelt van 6.7% naar 15-25%

---

## 🚨 CORE ARCHITECTUUR WIJZIGING

### Huidig Probleem (V16)
De Elemental agents zijn té selectief. Ether vereist harmony ≥ 0.45 + consensus, wat resulteert in 9.33% consensus rate en 350 trades in 6 jaar (te weinig).

### Nieuwe Architectuur (V17)
```
V17BacktestEngine
    ↓ (per dag)
VedAstroElementalAgentV17
    ├── VedAstro: Entry beslissing (BUY/SELL/HOLD)
    └── Elemental: Risk filtering (Ja/Nee)
            ↓
    Entry Execution met €2k cap + trailing stop
```

**Sleutel inzicht:** Gebruik VedAstro voor DE beslissing, Elemental voor het FILTEREN van risico.

---

## 🚨 PRIORITEIT 1: Creëer VedAstroElementalAgentV17

### Stap 1A: Maak de nieuwe agent klasse
Bestand: `backend/agents/elemental_agent_manager_v17.py`

```python
class VedAstroElementalAgentV17:
    """
    Hybride agent die VedAstro signalen combineert met Elemental risk management.
    """
    
    def __init__(self):
        # VedAstro componenten (reeds bestaand in backend.vedastro)
        from backend.vedastro import EnhancedAstroOrchestrator, TradingSignalGenerator
        self.astro_orchestrator = EnhancedAstroOrchestrator()
        self.signal_generator = TradingSignalGenerator()
        
        # Elemental risk componenten (uit V16 behouden)
        self.fire_agent = FireAgentV17()  # Alleen position sizing
        self.earth_agent = EarthAgentV17()  # Alleen entry blocking
        self.water_agent = WaterAgentV12()  # Regime check (preserve)
    
    async def evaluate_entry(self, symbol: str, current_price: float, 
                           cycle_date: datetime, portfolio_value: float) -> Optional[Dict]:
        """
        V17 Entry evaluatie:
        1. Vraag VedAstro analyse op
        2. Check Elemental risk filters
        3. Return entry dict of None
        """
        # 1. VEDASTRO ANALYSE (async - gebruik await)
        try:
            astro_analysis = await self.astro_orchestrator.analyze_asset(
                symbol=symbol, 
                current_price=current_price
            )
            signal = astro_analysis.trading_signal
        except Exception as e:
            logger.warning(f"VedAstro failed for {symbol}: {e}")
            return None
        
        # 2. FILTER: Alleen BUY signalen
        if signal.signal not in ['buy', 'strong_buy']:
            return None
        
        # 3. ELEMENTAL RISK CHECKS
        # Check 3a: Earth entry blocking (3-loss rule preserved)
        if not self.earth_agent.should_enter(symbol):
            return None
        
        # Check 3b: Water regime (TLT logic preserved)
        prices = list(self.fire_agent.price_history.get(symbol, []))
        macro_signal = self.water_agent.get_macro_signal(prices)
        if not self._regime_compatible(symbol, macro_signal):
            return None
        
        # Check 3c: Minimale VedAstro confidence
        if signal.confidence < 50:  # Minimaal 50% VedAstro confidence
            return None
        
        # 4. POSITION SIZING (Fire agent met €2k cap)
        position_size = self.fire_agent.calculate_position_size(
            symbol=symbol,
            portfolio_value=portfolio_value,
            harmony=signal.strength_score / 100,  # VedAstro score → harmony
            dominant_planet=self._get_dominant_planet(cycle_date)
        )
        
        # 5. RETURN ENTRY DICT
        return {
            "symbol": symbol,
            "action": "BUY",
            "entry_price": current_price * (1 + self.SLIPPAGE_PCT),
            "position_size": position_size,
            "vedastro_signal": signal.signal,
            "vedastro_confidence": signal.confidence,
            "vedastro_strength": signal.strength_score,
            "vedastro_risk": signal.risk_level,
            "dasha_context": signal.dasha_context,
            "primary_factors": signal.primary_factors,
        }
```

### Stap 1B: Vereenvoudigde Elemental Agents

**FireAgentV17** (alleen position sizing, geen confidence):
```python
class FireAgentV17:
    """V17: Alleen ATR-based position sizing, €2k cap."""
    
    MAX_POSITION_EUR = 2000.0
    
    def calculate_position_size(self, symbol, portfolio_value, harmony, dominant_planet):
        # V16 logica behouden, maar harmony komt nu van VedAstro (0-1)
        # ... (zelfde als V16) ...
        return min(calculated_size, portfolio_value * 0.02, self.MAX_POSITION_EUR)
```

**EarthAgentV17** (alleen entry blocking, geen confidence):
```python
class EarthAgentV17:
    """V17: Alleen 3-loss entry blocking + trailing stop tracking."""
    
    MAX_HOLD_DAYS = 60
    
    # 3-loss rule (behouden van V16)
    def should_enter(self, symbol: str) -> bool:
        recent = list(self.symbol_memory.get(symbol, []))
        if len(recent) >= 3:
            last_three = recent[-3:]
            if all(not t['win'] for t in last_three):
                return False
        return True
    
    # Trailing stop logic (behouden van V16)
    def update_unrealized_pnl(self, symbol: str, pnl_pct: float):
        # ... (zelfde als V16) ...
    
    def check_trailing_stop(self, symbol: str, current_pnl_pct: float) -> bool:
        # ... (zelfde als V16) ...
```

---

## 🚨 PRIORITEIT 2: Update Backtest Engine voor Async

### Stap 2A: Maak engine async-compatibel
Bestand: `scripts/backtest_elemental_v17.py`

```python
import asyncio
from backend.agents.elemental_agent_manager_v17 import VedAstroElementalAgentV17

class V17BacktestEngine:
    def __init__(self, symbols, start_date, end_date, initial_capital=100000.0):
        # ... existing init ...
        self.agent_manager = VedAstroElementalAgentV17()
        self.astro_cache = {}  # Cache voor VedAstro resultaten per dag
    
    async def run_backtest(self):
        """V17: Async backtest met VedAstro integratie."""
        for trading_date in self._trading_dates:
            await self._process_day(trading_date)
    
    async def _process_day(self, trading_date: datetime, price_data: dict):
        """V17: Daily processing met VedAstro."""
        # Cycle counting (preserve)
        self.agent_manager.increment_cycle()
        
        # Position reviews (preserve from V16)
        await self._review_positions(trading_date, price_data)
        
        # Entry evaluations (NIEUW: async VedAstro)
        for symbol in self.symbols:
            if symbol in self.open_positions:
                continue
            
            current_price = self._get_price_for_date(price_data, symbol, trading_date)
            if not current_price:
                continue
            
            portfolio_value = self._calculate_portfolio_value(price_data, trading_date)
            
            # V17: ASYNC VedAstro + Elemental evaluatie
            entry_result = await self.agent_manager.evaluate_entry(
                symbol=symbol,
                current_price=current_price,
                cycle_date=trading_date,
                portfolio_value=portfolio_value
            )
            
            if entry_result:
                self._execute_entry(entry_result, trading_date, price_data)
```

### Stap 2B: Caching voor Performance

```python
def _get_cached_astro_or_calculate(self, symbol: str, date: datetime, price: float):
    """Cache VedAstro berekeningen per dag om performance te verbeteren."""
    cache_key = f"{symbol}_{date.strftime('%Y-%m-%d')}"
    
    if cache_key not in self.astro_cache:
        # Bereken en cache
        self.astro_cache[cache_key] = await self.agent_manager.astro_orchestrator.analyze_asset(symbol, price)
    
    return self.astro_cache[cache_key]
```

---

## 🚨 PRIORITEIT 3: Aggressieve Threshold Kalibratie

Verdere verlaging om consensus rate te verhogen:

| Parameter | V16 | **V17** | Impact |
|-----------|-----|---------|--------|
| Fire floor | 0.35 | **0.30** | Meer trades |
| Earth floor | 0.45 | **0.40** | Sneller herstel |
| VedAstro min confidence | N/A | **50** | Filter zwakke signalen |
| VedAstro entry signals | N/A | **buy/strong_buy** | Alleen long |

---

## 🚨 PRIORITEIT 4: Nieuwe Exit Reasons

Voeg VedAstro-specifieke exit reasons toe:

```python
# In _execute_exit():
if reason == 'vedastro_sell_signal':
    self.agent_manager.position_review_exits += 1
    
# Nieuwe exit evaluatie in _review_positions():
async def _review_positions(self, date, price_data):
    for symbol, position in self.open_positions.items():
        # Bestaande checks (time_based, trailing_stop) preserve
        
        # NIEUW: VedAstro SELL signal check
        astro = await self._get_cached_astro_or_calculate(symbol, date, current_price)
        if astro.trading_signal.signal in ['sell', 'strong_sell']:
            if astro.trading_signal.confidence > 60:
                return True, 'vedastro_sell_signal'
```

---

## 🛑 STRICT PRESERVATION (DO NOT MODIFY)

Deze componenten blijven EXACT zoals in V16:

1. **Daily cycle counting**: `increment_cycle()` blijft 1x per dag
2. **€2,000 position cap**: `MAX_POSITION_EUR = 2000.0`
3. **Trailing stop**: +40% activeert, -15% exit
4. **60-day failsafe**: `MAX_HOLD_DAYS = 60`
5. **Water TLT logic**: Bond inverse regime shift
6. **AAVE exclusion**: Blijft uit universe
7. **Hedge symbols**: SH, PSQ, RWM, TBF blijven beschikbaar

---

## ✅ ACCEPTATIE CRITERIA (Definition of Done)

Na V17 implementatie moet de backtest (2020-2026) tonen:

| Metric | V16 Baseline | V17 Doel | Status |
|--------|--------------|----------|--------|
| Consensus Rate | 9.33% | **40-60%** | ⬜ |
| Execute Rate | 6.70% | **15-25%** | ⬜ |
| Total Trades | 350 | **1000-1500** | ⬜ |
| VedAstro Entries | 0% | **>50%** | ⬜ |
| Return | +2.11% | **+40-80%** | ⬜ |
| Max Drawdown | -5.15% | **<-15%** | ⬜ |

**Verificatie stappen:**
1. Draai `python scripts/backtest_elemental_v17_full.py`
2. Check dat `vedastro_signal` in exit reasons voorkomt
3. Check dat AAVE afwezig is
4. Check dat hedge entries > 0 zijn
5. Controleer position sizes ≤ €2,000

---

## 📁 Te Creëren/Bijwerken Bestanden

### Nieuwe Bestanden
1. `backend/agents/elemental_agent_manager_v17.py` - Hoofdagent
2. `scripts/backtest_elemental_v17.py` - Engine
3. `scripts/backtest_elemental_v17_full.py` - Full run script

### Bijwerken (alleen imports/namen)
4. `scripts/analyze_v17.py` - Analysis script (kopie van v16)

---

## 🎯 SAMENVATTING

V17 transformeert het systeem van een **starre Elemental-only** naar een **flexibele VedAstro-gedreven** approach:

- **VedAstro** bepaalt WAAROM we traden (astro timing)
- **Elemental** bepaalt HOEVEEL we riskeren (€2k cap, stops)
- **Resultaat**: Meer trades, beter geïnformeerd, zelfde risk management

**Belangrijk**: De core filosofie (Samkhya 5-elementen) blijft behouden, maar de implementatie wordt pragmatischer door VedAstro's superieure timing informatie.

**Klaar voor implementatie!** 🚀🔮
