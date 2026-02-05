import pytest
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# --- FIX: Mock aiokafka module BEFORE importing KafkaBroker ---
# Dit is nodig omdat de echte module anders ImportError gooit bij import
mock_aiokafka = MagicMock()
mock_aiokafka.AIOKafkaProducer = MagicMock()
mock_aiokafka.AIOKafkaConsumer = MagicMock()
sys.modules["aiokafka"] = mock_aiokafka

# Nu kunnen we veilig importeren
from backend.events.kafka_broker import KafkaBroker

@pytest.mark.asyncio
async def test_kafka_connect_fails():
    """Test dat de broker een error gooit als Kafka onbereikbaar is."""
    # We moeten patchen op de plek waar het GEBRUIKT wordt (backend.events.kafka_broker)
    # niet waar het vandaan komt (aiokafka) omdat we die net gemockt hebben
    
    # Setup de mock producer om te falen bij start
    mock_producer_instance = AsyncMock()
    mock_producer_instance.start.side_effect = Exception("Connection Refused")
    
    with patch("backend.events.kafka_broker.AIOKafkaProducer", return_value=mock_producer_instance):
        broker = KafkaBroker(bootstrap_servers="localhost:9092")
        
        with pytest.raises(Exception, match="Connection Refused"):
            await broker.connect()

@pytest.mark.asyncio
async def test_publish_without_connect():
    """Test dat publish faalt als er geen verbinding is."""
    # Hier hoeven we niks te patchen, we testen de interne logica
    with patch("backend.events.kafka_broker.AIOKafkaProducer"): # Zorg dat init slaagt
        broker = KafkaBroker(bootstrap_servers="localhost:9092")
        
        with pytest.raises(RuntimeError, match="Producer not connected"):
            await broker.publish("test_topic", "key", {"data": 123})

@pytest.mark.asyncio
async def test_kafka_publish_success():
    """Test succesvolle publicatie."""
    mock_producer_instance = AsyncMock()
    
    with patch("backend.events.kafka_broker.AIOKafkaProducer", return_value=mock_producer_instance):
        broker = KafkaBroker(bootstrap_servers="mock_server")
        await broker.connect()
        
        await broker.publish("trades", "BTC", {"price": 100})
        
        # Verifieer dat send_and_wait is aangeroepen
        mock_producer_instance.send_and_wait.assert_called_once()
        args = mock_producer_instance.send_and_wait.call_args
        assert args[0][0] == "trades" # Topic check
        
        await broker.disconnect()
        mock_producer_instance.stop.assert_called_once()