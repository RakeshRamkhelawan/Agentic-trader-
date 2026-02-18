from unittest.mock import MagicMock, patch

import pytest

from backend.core.memory_agent import MemoryAgent


@pytest.fixture
def mock_chroma_client():
    client = MagicMock()
    return client


@pytest.fixture
def memory_agent(mock_chroma_client):
    # Mock settings to avoid import errors or env var issues if settings is used in init
    with patch("backend.core.memory_agent.settings") as mock_settings:
        mock_settings.CHROMA_HOST = "localhost"
        mock_settings.CHROMA_PORT = 8000
        agent = MemoryAgent(client=mock_chroma_client, collection_name="test_thoughts")
    return agent


def test_memory_agent_init(memory_agent, mock_chroma_client):
    assert memory_agent.client == mock_chroma_client
    assert memory_agent.base_collection_name == "test_thoughts"
    assert memory_agent._collections == {}


def test_get_collection_default_tenant(memory_agent, mock_chroma_client):
    # Test without tenant context (should default to "default")
    with patch(
        "backend.core.memory_agent.get_current_tenant_optional", return_value=None
    ):
        collection = memory_agent._get_collection()

        mock_chroma_client.get_or_create_collection.assert_called_with(
            name="default_test_thoughts", metadata={"hnsw:space": "cosine"}
        )
        assert "default_test_thoughts" in memory_agent._collections


def test_get_collection_specific_tenant(memory_agent, mock_chroma_client):
    # Test with tenant context
    with patch(
        "backend.core.memory_agent.get_current_tenant_optional",
        return_value="tenant-abc",
    ):
        collection = memory_agent._get_collection()

        mock_chroma_client.get_or_create_collection.assert_called_with(
            name="tenant-abc_test_thoughts", metadata={"hnsw:space": "cosine"}
        )
        assert "tenant-abc_test_thoughts" in memory_agent._collections


def test_store_thought_injects_tenant_id(memory_agent, mock_chroma_client):
    mock_collection = MagicMock()
    memory_agent._collections["tenant-xyz_test_thoughts"] = mock_collection

    with patch(
        "backend.core.memory_agent.get_current_tenant_optional",
        return_value="tenant-xyz",
    ):
        # We need to ensure _get_collection returns the mock
        with patch.object(
            memory_agent, "_get_collection", return_value=mock_collection
        ) as mock_get_coll:
            memory_agent.store_thought("agent-1", "thought text")

            mock_get_coll.assert_called_once()
            mock_collection.add.assert_called_once()
            call_args = mock_collection.add.call_args
            # Check metadata
            metadatas = call_args[1]["metadatas"]
            assert metadatas[0]["tenant_id"] == "tenant-xyz"
            assert metadatas[0]["agent_id"] == "agent-1"


def test_recall_thoughts_uses_tenant_collection(memory_agent, mock_chroma_client):
    mock_collection = MagicMock()
    mock_collection.query.return_value = {"documents": [], "metadatas": [], "ids": []}

    with patch(
        "backend.core.memory_agent.get_current_tenant_optional",
        return_value="tenant-xyz",
    ):
        with patch.object(
            memory_agent, "_get_collection", return_value=mock_collection
        ) as mock_get_coll:
            memory_agent.recall_thoughts("query")

            mock_get_coll.assert_called_once()
            mock_collection.query.assert_called_once()
