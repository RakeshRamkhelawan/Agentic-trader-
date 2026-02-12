import pytest
import chromadb
from backend.services.cognitive_orchestrator import MemoryAgent

# --- FIXTURE ---
@pytest.fixture
def memory_agent():
    # We gebruiken een lokale, in-memory Chroma client voor de test
    client = chromadb.Client()
    # Gebruik unieke naam per test run (of reset)
    import uuid
    unique_name = f"test_collection_{uuid.uuid4()}"
    return MemoryAgent(client=client, collection_name=unique_name)

# --- TESTS ---

def test_store_and_recall_thought(memory_agent):
    """Happy Path: Sla een gedachte op en haal hem terug op relevantie."""
    
    # 1. Store
    memory_agent.store_thought(
        agent_id="sentiment_v1",
        text="Market is extremely bearish due to high inflation news.",
        metadata={"sentiment": "negative", "confidence": 0.9}
    )
    
    # 2. Recall (RAG)
    # Zoek naar iets dat semantisch lijkt op "inflation"
    results = memory_agent.recall_thoughts(query="inflation impact", limit=1)
    
    assert len(results) == 1
    # Check of de tekst overeenkomt
    assert "bearish" in results[0]['document']
    assert results[0]['metadata']['sentiment'] == "negative"

def test_recall_empty_memory(memory_agent):
    """Unhappy Path: Zoeken in leeg geheugen mag niet crashen."""
    results = memory_agent.recall_thoughts(query="nothing here", limit=5)
    assert len(results) == 0
