# FastAPI + Redis Event Patterns

Common patterns for FastAPI routes with Redis Streams event publishing.

## Event Bus Setup

```python
from backend.events.event_bus import EventBus

event_bus = EventBus()

# Publish event
await event_bus.publish(
    stream="trading.events",
    event={
        "type": "order_executed",
        "data": order_data,
        "timestamp": datetime.now(UTC).isoformat()
    }
)
```

## Standard Route Pattern

```python
@router.post("/orders", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    user: dict = Depends(require_auth)
):
    # 1. Validate
    if order.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    # 2. Create
    created = await create_in_db(order)

    # 3. Publish event
    await event_bus.publish("orders", {
        "type": "created",
        "order_id": created.id,
        "user_id": user['id']
    })

    return created
```

## Event Consumer Pattern

```python
from backend.events.event_bus import EventBus

async def process_trading_events():
    event_bus = EventBus()

    async for event in event_bus.subscribe("trading.events"):
        if event['type'] == 'order_executed':
            await update_portfolio(event['data'])
        elif event['type'] == 'price_alert':
            await send_notification(event['data'])
```

## Background Tasks

```python
from fastapi import BackgroundTasks

@router.post("/analyze")
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_auth)
):
    # Return immediately, process in background
    background_tasks.add_task(run_analysis, request)

    return {"status": "processing", "job_id": generate_id()}
```

## Dependency Injection

```python
# backend/api/deps.py
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

async def get_event_bus():
    return EventBus()

# Use in routes
@router.get("/data")
async def get_data(
    session: AsyncSession = Depends(get_db_session),
    event_bus: EventBus = Depends(get_event_bus)
):
    ...
```

## Error Handling

```python
from backend.api.error_handlers import handle_api_error

@router.post("/trade")
async def execute_trade(request: TradeRequest):
    try:
        result = await execute(request)
        return result
    except InsufficientFundsError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient funds: {e}"
        )
    except Exception as e:
        # Log and return generic error
        logger.error(f"Trade failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Trade execution failed"
        )
```

## WebSocket with Events

```python
@router.websocket("/ws/market")
async def market_websocket(websocket: WebSocket):
    await websocket.accept()
    event_bus = EventBus()

    # Subscribe to market events
    async for event in event_bus.subscribe("market.data"):
        await websocket.send_json(event)
```
