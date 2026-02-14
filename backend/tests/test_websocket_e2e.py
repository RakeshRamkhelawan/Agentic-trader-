"""
End-to-end WebSocket integration tests.

Tests the full stack: Backend WebSocket server <-> Frontend WebSocket client simulation.

Run with: pytest backend/tests/test_websocket_e2e.py -v
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest

# ============================================
# WebSocket Manager Tests
# ============================================

class TestWebSocketManager:
    """Tests for the WebSocket manager."""
    
    @pytest.fixture
    def ws_manager(self):
        """Create a fresh WebSocket manager for each test."""
        from backend.api.websocket_manager import WebSocketManager
        return WebSocketManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.receive_json = AsyncMock()
        return ws
    
    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self, ws_manager, mock_websocket):
        """Test basic connection and disconnection."""
        # Connect
        await ws_manager.connect(
            websocket=mock_websocket,
            connection_id="test-conn-1",
            tenant_id="tenant-1",
            account_id="account-1"
        )
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()
        
        # Verify connection is tracked
        assert "test-conn-1" in ws_manager.connections
        assert ws_manager.connections["test-conn-1"].tenant_id == "tenant-1"
        
        # Disconnect
        await ws_manager.disconnect("test-conn-1")
        assert "test-conn-1" not in ws_manager.connections
    
    @pytest.mark.asyncio
    async def test_subscribe_to_channel(self, ws_manager, mock_websocket):
        """Test subscribing to a channel."""
        await ws_manager.connect(
            websocket=mock_websocket,
            connection_id="test-conn-1",
            tenant_id="tenant-1",
            account_id="account-1"
        )
        
        # Subscribe to orderbook channel
        success = await ws_manager.subscribe("test-conn-1", "orderbook.BTC-EUR")
        
        assert success
        assert "orderbook.BTC-EUR" in ws_manager.connections["test-conn-1"].subscriptions
        assert "test-conn-1" in ws_manager.channel_subscribers.get("orderbook.BTC-EUR", set())
        
        # Cleanup
        await ws_manager.disconnect("test-conn-1")
    
    @pytest.mark.asyncio
    async def test_broadcast_to_channel(self, ws_manager, mock_websocket):
        """Test broadcasting to channel subscribers."""
        # Connect and subscribe
        await ws_manager.connect(
            websocket=mock_websocket,
            connection_id="test-conn-1",
            tenant_id="tenant-1",
            account_id="account-1"
        )
        await ws_manager.subscribe("test-conn-1", "orderbook.BTC-EUR")
        
        # Reset mock to clear connection confirmation message
        mock_websocket.send_json.reset_mock()
        
        # Broadcast orderbook update
        sent_count = await ws_manager.broadcast_to_channel(
            channel="orderbook.BTC-EUR",
            message={"bids": [[45000, 1.5]], "asks": [[45001, 2.0]]},
            message_type="snapshot"
        )
        
        assert sent_count == 1
        
        # Verify message was sent
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["channel"] == "orderbook.BTC-EUR"
        assert call_args["type"] == "snapshot"
        assert call_args["data"]["bids"] == [[45000, 1.5]]
        
        # Cleanup
        await ws_manager.disconnect("test-conn-1")
    
    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self, ws_manager):
        """Test that tenant isolation works for orders channel."""
        mock_ws1 = AsyncMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_json = AsyncMock()
        
        mock_ws2 = AsyncMock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_json = AsyncMock()
        
        # Connect two users from different accounts
        await ws_manager.connect(
            websocket=mock_ws1,
            connection_id="conn-1",
            tenant_id="tenant-1",
            account_id="account-1"
        )
        await ws_manager.connect(
            websocket=mock_ws2,
            connection_id="conn-2",
            tenant_id="tenant-1",
            account_id="account-2"
        )
        
        # Subscribe both to orders (should create separate channels)
        await ws_manager.subscribe("conn-1", "orders")
        await ws_manager.subscribe("conn-2", "orders")
        
        # Verify separate channels were created
        assert "orders.account-1" in ws_manager.channel_subscribers
        assert "orders.account-2" in ws_manager.channel_subscribers
        
        # Reset mocks
        mock_ws1.send_json.reset_mock()
        mock_ws2.send_json.reset_mock()
        
        # Broadcast order update only to account-1
        await ws_manager.broadcast_order_update(
            account_id="account-1",
            order_data={"order_id": "123", "status": "filled"}
        )
        
        # Only conn-1 should receive the message
        assert mock_ws1.send_json.called
        assert not mock_ws2.send_json.called
        
        # Cleanup
        await ws_manager.disconnect("conn-1")
        await ws_manager.disconnect("conn-2")
    
    @pytest.mark.asyncio
    async def test_handle_client_message_subscribe(self, ws_manager, mock_websocket):
        """Test handling subscribe message from client."""
        await ws_manager.connect(
            websocket=mock_websocket,
            connection_id="test-conn-1",
            tenant_id="tenant-1",
            account_id="account-1"
        )
        
        # Handle subscribe message
        await ws_manager.handle_client_message(
            connection_id="test-conn-1",
            message={"type": "subscribe", "channel": "ticker.BTC-EUR"}
        )
        
        assert "ticker.BTC-EUR" in ws_manager.connections["test-conn-1"].subscriptions
        
        # Cleanup
        await ws_manager.disconnect("test-conn-1")
    
    @pytest.mark.asyncio
    async def test_handle_ping_pong(self, ws_manager, mock_websocket):
        """Test ping/pong heartbeat."""
        await ws_manager.connect(
            websocket=mock_websocket,
            connection_id="test-conn-1",
            tenant_id="tenant-1",
            account_id="account-1"
        )
        
        # Reset mock
        mock_websocket.send_json.reset_mock()
        
        # Send ping
        await ws_manager.handle_client_message(
            connection_id="test-conn-1",
            message={"type": "ping"}
        )
        
        # Verify pong was sent
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "pong"
        
        # Cleanup
        await ws_manager.disconnect("test-conn-1")
    
    @pytest.mark.asyncio
    async def test_get_stats(self, ws_manager, mock_websocket):
        """Test statistics retrieval."""
        await ws_manager.connect(
            websocket=mock_websocket,
            connection_id="test-conn-1",
            tenant_id="tenant-1",
            account_id="account-1"
        )
        await ws_manager.subscribe("test-conn-1", "orderbook.BTC-EUR")
        await ws_manager.subscribe("test-conn-1", "ticker.BTC-EUR")
        
        stats = ws_manager.get_stats()
        
        assert stats["total_connections"] == 1
        assert stats["total_channels"] == 2
        assert "orderbook.BTC-EUR" in stats["channels"]
        assert "ticker.BTC-EUR" in stats["channels"]
        
        # Cleanup
        await ws_manager.disconnect("test-conn-1")


# ============================================
# Market Data Streamer Tests
# ============================================

class TestMarketDataStreamer:
    """Tests for the market data streamer."""
    
    @pytest.fixture
    def streamer(self):
        """Create a fresh market data streamer for each test."""
        from backend.services.market_data_streamer import MarketDataStreamer
        return MarketDataStreamer()
    
    @pytest.mark.asyncio
    async def test_start_and_stop_stream(self, streamer):
        """Test starting and stopping a stream."""
        # Start stream
        success = await streamer.start_stream("BTC-EUR")
        assert success
        assert "binance.BTC-EUR" in streamer.active_streams
        
        # Start same stream again (should return True, already running)
        success = await streamer.start_stream("BTC-EUR")
        assert success
        
        # Stop stream
        success = await streamer.stop_stream("BTC-EUR")
        assert success
        assert "binance.BTC-EUR" not in streamer.active_streams
        
        # Stop non-existent stream
        success = await streamer.stop_stream("XRP-EUR")
        assert not success
    
    @pytest.mark.asyncio
    async def test_mock_data_generation(self, streamer):
        """Test that mock data is generated correctly."""
        # Create mock WebSocket manager
        mock_ws_manager = AsyncMock()
        mock_ws_manager.broadcast_orderbook = AsyncMock(return_value=1)
        mock_ws_manager.broadcast_ticker = AsyncMock(return_value=1)
        
        streamer.set_ws_manager(mock_ws_manager)
        
        # Start stream
        await streamer.start_stream("BTC-EUR")
        
        # Wait for a few updates
        await asyncio.sleep(0.3)
        
        # Stop stream
        await streamer.stop_stream("BTC-EUR")
        
        # Verify broadcasts were made
        assert mock_ws_manager.broadcast_orderbook.called
        assert mock_ws_manager.broadcast_ticker.called
        
        # Cleanup
        await streamer.close()


# ============================================
# Integration Tests
# ============================================

class TestWebSocketIntegration:
    """Full integration tests simulating frontend-backend communication."""
    
    @pytest.mark.asyncio
    async def test_full_orderbook_flow(self):
        """Test complete orderbook subscription flow."""
        from backend.api.websocket_manager import WebSocketManager
        from backend.services.market_data_streamer import MarketDataStreamer

        # Setup
        ws_manager = WebSocketManager()
        streamer = MarketDataStreamer()
        streamer.set_ws_manager(ws_manager)
        
        # Simulate client connection
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        
        await ws_manager.connect(
            websocket=mock_ws,
            connection_id="client-1",
            tenant_id="tenant-1",
            account_id="account-1"
        )
        
        # Subscribe to orderbook
        await ws_manager.subscribe("client-1", "orderbook.BTC-EUR")
        
        # Start streaming
        await streamer.start_stream("BTC-EUR")
        
        # Wait for data
        await asyncio.sleep(0.2)
        
        # Verify client received data
        assert mock_ws.send_json.call_count >= 2  # Connection + orderbook data
        
        # Cleanup
        await streamer.close()
        await ws_manager.disconnect("client-1")
    
    @pytest.mark.asyncio
    async def test_multiple_clients_same_channel(self):
        """Test multiple clients subscribing to the same channel."""
        from backend.api.websocket_manager import WebSocketManager
        
        ws_manager = WebSocketManager()
        
        # Connect multiple clients
        clients = []
        for i in range(3):
            mock_ws = AsyncMock()
            mock_ws.accept = AsyncMock()
            mock_ws.send_json = AsyncMock()
            
            await ws_manager.connect(
                websocket=mock_ws,
                connection_id=f"client-{i}",
                tenant_id="tenant-1",
                account_id=f"account-{i}"
            )
            await ws_manager.subscribe(f"client-{i}", "orderbook.BTC-EUR")
            clients.append(mock_ws)
        
        # Reset mocks
        for client in clients:
            client.send_json.reset_mock()
        
        # Broadcast to all
        sent_count = await ws_manager.broadcast_to_channel(
            channel="orderbook.BTC-EUR",
            message={"bids": [[45000, 1.0]], "asks": [[45001, 1.0]]},
            message_type="delta"
        )
        
        assert sent_count == 3
        
        for client in clients:
            assert client.send_json.called
        
        # Cleanup
        for i in range(3):
            await ws_manager.disconnect(f"client-{i}")


# ============================================
# Protocol Conformance Tests
# ============================================

class TestWebSocketProtocol:
    """Tests to verify frontend-backend protocol compatibility."""
    
    @pytest.mark.asyncio
    async def test_message_format_matches_frontend_expectations(self):
        """Verify server messages match frontend hook expectations."""
        from backend.api.websocket_manager import WebSocketManager
        
        ws_manager = WebSocketManager()
        
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        
        await ws_manager.connect(
            websocket=mock_ws,
            connection_id="client-1",
            tenant_id="tenant-1",
            account_id="account-1"
        )
        await ws_manager.subscribe("client-1", "orderbook.BTC-EUR")
        
        mock_ws.send_json.reset_mock()
        
        # Broadcast orderbook
        await ws_manager.broadcast_orderbook(
            symbol="BTC-EUR",
            bids=[[45000.5, 1.5], [44999.0, 2.0]],
            asks=[[45001.0, 1.0], [45002.5, 3.0]],
            is_snapshot=True
        )
        
        # Verify message format
        message = mock_ws.send_json.call_args[0][0]
        
        # Frontend expects: { channel, type, data: { bids, asks }, timestamp }
        assert "channel" in message
        assert "type" in message
        assert "data" in message
        assert "timestamp" in message
        
        assert message["channel"] == "orderbook.BTC-EUR"
        assert message["type"] == "snapshot"  # Frontend uses "snapshot" | "delta"
        assert "bids" in message["data"]
        assert "asks" in message["data"]
        
        # Bids should be [price, size] arrays
        assert len(message["data"]["bids"]) == 2
        assert message["data"]["bids"][0] == [45000.5, 1.5]
        
        # Cleanup
        await ws_manager.disconnect("client-1")
    
    @pytest.mark.asyncio
    async def test_ticker_message_format(self):
        """Verify ticker messages match frontend useTicker expectations."""
        from backend.api.websocket_manager import WebSocketManager
        
        ws_manager = WebSocketManager()
        
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        
        await ws_manager.connect(
            websocket=mock_ws,
            connection_id="client-1",
            tenant_id="tenant-1",
            account_id="account-1"
        )
        await ws_manager.subscribe("client-1", "ticker.BTC-EUR")
        
        mock_ws.send_json.reset_mock()
        
        # Broadcast ticker
        await ws_manager.broadcast_ticker(
            symbol="BTC-EUR",
            bid=45000.0,
            ask=45001.0,
            last=45000.5,
            volume_24h=1000.0,
            change_24h=500.0,
            change_percent_24h=1.12,
            high_24h=46000.0,
            low_24h=44000.0
        )
        
        message = mock_ws.send_json.call_args[0][0]
        
        # Frontend useTicker expects these fields
        assert message["channel"] == "ticker.BTC-EUR"
        assert message["type"] == "update"
        
        data = message["data"]
        assert data["symbol"] == "BTC-EUR"
        assert data["bid"] == 45000.0
        assert data["ask"] == 45001.0
        assert data["last"] == 45000.5
        assert data["volume_24h"] == 1000.0
        assert data["change_24h"] == 500.0
        assert data["change_percent_24h"] == 1.12
        assert data["high_24h"] == 46000.0
        assert data["low_24h"] == 44000.0
        assert "timestamp" in data
        
        # Cleanup
        await ws_manager.disconnect("client-1")
    
    @pytest.mark.asyncio
    async def test_order_update_message_format(self):
        """Verify order update messages match frontend useOrders expectations."""
        from backend.api.websocket_manager import WebSocketManager
        
        ws_manager = WebSocketManager()
        
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()
        
        await ws_manager.connect(
            websocket=mock_ws,
            connection_id="client-1",
            tenant_id="tenant-1",
            account_id="account-1"
        )
        await ws_manager.subscribe("client-1", "orders")
        
        mock_ws.send_json.reset_mock()
        
        # Broadcast order update
        await ws_manager.broadcast_order_update(
            account_id="account-1",
            order_data={
                "order_id": "ord-123",
                "client_order_id": "client-ord-456",
                "symbol": "BTC-EUR",
                "side": "buy",
                "type": "limit",
                "status": "filled",
                "quantity": 1.5,
                "filled_quantity": 1.5,
                "remaining_quantity": 0,
                "price": 45000.0,
                "average_price": 44999.5,
                "created_at": "2026-02-06T01:00:00Z",
                "updated_at": "2026-02-06T01:01:00Z"
            }
        )
        
        message = mock_ws.send_json.call_args[0][0]
        
        # Verify format matches frontend expectations
        assert message["channel"] == "orders.account-1"
        assert message["type"] == "update"
        
        data = message["data"]
        assert data["order_id"] == "ord-123"
        assert data["status"] == "filled"
        assert data["side"] == "buy"
        
        # Cleanup
        await ws_manager.disconnect("client-1")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
