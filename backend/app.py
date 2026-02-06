"""
Application startup with WebSocket support.

Run with: uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from backend.api.gateway import APIGateway
from backend.api.websocket_manager import ws_manager
from backend.services.market_data_streamer import market_streamer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    """Application lifespan handler for startup/shutdown."""
    logger.info("Starting Agentic Trader API...")
    
    # Connect market streamer to WebSocket manager
    market_streamer.set_ws_manager(ws_manager)
    
    # Start heartbeat monitoring
    await ws_manager.start_heartbeat(interval_seconds=30)
    
    # Start default market streams (can be configured)
    default_symbols = ["BTC-EUR", "ETH-EUR"]
    for symbol in default_symbols:
        await market_streamer.start_stream(symbol)
    
    logger.info("API ready - WebSocket streaming active")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down...")
    await market_streamer.close()


# Create API gateway
gateway = APIGateway()
app = gateway.app

# Add lifespan handler
app.router.lifespan_context = lifespan
