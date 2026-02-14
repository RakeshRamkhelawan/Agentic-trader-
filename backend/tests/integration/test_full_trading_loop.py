from datetime import datetime
from unittest.mock import MagicMock

import pytest

from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.execution.smart_order_router import SmartOrderRouter
from backend.risk.validators import RiskValidator, RiskViolationError
from backend.schemas.market_data import MarketTick
from backend.schemas.orders import (OrderRequest, OrderSide, OrderStatus,
                                    OrderType)
# Importeer alle componenten die we hebben gebouwd
from backend.services.cognitive_orchestrator import (AgentMessage,
                                                     MarketRegime,
                                                     RegimeDetector)

# --- FIXTURES VOOR DE HELE KETEN ---

@pytest.fixture
def trading_system():
    """Bouwt de hele keten op in-memory."""
    
    # 1. Execution Layer
    portfolio = ShadowPortfolioManager(initial_cash=100000.0)
    router = SmartOrderRouter()
    # Registreer de portfolio als de 'broker' voor alles
    router.register_adapter("shadow_broker", portfolio, ["BTC-EUR"])
    
    # 2. Risk Layer
    risk_guard = RiskValidator(max_order_size=10000.0, max_daily_loss=500.0)
    
    # 3. Cognitive Layer
    brain = RegimeDetector()
    
    return {
        "portfolio": portfolio,
        "router": router,
        "risk": risk_guard,
        "brain": brain
    }

# --- HAPPY PATH: THE BULL RUN ---

@pytest.mark.asyncio
async def test_e2e_bull_run_execution(trading_system):
    """
    Scenario:
    1. Tick: BTC=50k, Low Vol.
    2. Brain: Bull Market.
    3. Agent: Signal BUY.
    4. Execution: Success.
    """
    sys = trading_system
    
    # Stap 1: Market Data
    tick = MarketTick(symbol="BTC-EUR", price=50000.0, volume=1.0)
    # Update de 'exchange' prijs zodat onze order kan vullen
    sys["portfolio"].update_price("BTC-EUR", 50000.0)
    
    # Stap 2: Cognition
    # SMA=49k, Price=50k -> Bull
    regime = sys["brain"].detect(price=tick.price, sma_50=49000.0, volatility=0.01)
    assert regime == MarketRegime.BULL
    
    # Stap 3: Agent Decision (Simulatie)
    # Als regime == BULL, dan kopen we
    if regime == MarketRegime.BULL:
        order = OrderRequest(
            symbol="BTC-EUR",
            qty=0.1, # 5000 EUR value
            side=OrderSide.BUY,
            order_type=OrderType.MARKET
        )
    
    # Stap 4: Risk Check
    # Moet slagen want 5000 < 10000 limiet
    sys["risk"].validate_order(order, current_price=tick.price)
    
    # Stap 5: Execution
    result = await sys["router"].route_and_execute(order)
    
    # Assertions
    assert result.status == OrderStatus.FILLED
    assert result.filled_qty == 0.1
    assert result.avg_price == 50000.0
    
    # Check Cash: 100k - 5k = 95k
    balance = await sys["portfolio"].get_balance()
    assert balance["EUR"] == 95000.0
    assert balance["BTC-EUR"] == 0.1

# --- UNHAPPY PATH: THE CRASH ---

@pytest.mark.asyncio
async def test_e2e_kill_switch_activation(trading_system):
    """
    Scenario:
    1. Tick: BTC=50k, EXTREME VOLATILITY (10%).
    2. Brain: Detects VOLATILE -> Triggers Kill Switch.
    3. Agent: Probeert toch te kopen (eigenwijs).
    4. Risk: BLOCKS order.
    """
    sys = trading_system
    
    # Stap 1: Market Data
    tick = MarketTick(symbol="BTC-EUR", price=50000.0, volume=50.0)
    
    # Stap 2: Cognition
    # Volatility 0.10 (> 0.05 limit)
    regime = sys["brain"].detect(price=tick.price, sma_50=49000.0, volatility=0.10)
    assert regime == MarketRegime.VOLATILE
    
    # De Orchestrator zou nu de kill switch moeten omzetten
    if regime == MarketRegime.VOLATILE:
        sys["risk"].activate_kill_switch()
        
    # Stap 3: Agent probeert toch
    order = OrderRequest(symbol="BTC-EUR", qty=0.01, side=OrderSide.BUY, order_type=OrderType.MARKET)
    
    # Stap 4: Risk Check -> BOOM
    with pytest.raises(RiskViolationError, match="KILL SWITCH ACTIVE"):
        sys["risk"].validate_order(order, current_price=tick.price)
        
    # Check dat er GEEN order naar de router is gegaan (impliciet, want we crashten ervoor)
    balance = await sys["portfolio"].get_balance()
    assert balance["EUR"] == 100000.0 # Geld is veilig
