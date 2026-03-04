"""
Unit tests for RAG Vector Memory.

Tests vector storage, similarity search, and systemic failure scenarios.
"""

from unittest.mock import AsyncMock, patch

import numpy as np
import pytest

from backend.rag.vector_memory import VectorMemory, VectorStoreError


@pytest.fixture
async def mock_vector_memory():
    """Fixture for in-memory vector store (using SQLite for tests)."""
    # Note: SQLite doesn't support pgvector, so we'll use mocks for actual tests
    # This is a placeholder showing the interface
    vm = VectorMemory(connection_string="sqlite+aiosqlite:///:memory:", embedding_dim=384)
    yield vm
    await vm.close()


class TestVectorMemoryInit:
    """Tests for VectorMemory initialization."""

    def test_valid_initialization(self):
        """Happy path: Valid initialization."""
        vm = VectorMemory(
            connection_string="postgresql+asyncpg://user:pass@localhost/db", embedding_dim=384
        )
        assert vm.embedding_dim == 384
        assert vm.connection_string is not None

    @pytest.mark.asyncio
    async def test_database_down_resilience(self):
        """Systemic Unhappy Path: Database unreachable."""
        vm = VectorMemory(connection_string="postgresql+asyncpg://bad:port@nonexistent:9999/db")

        # Attempting operations should raise VectorStoreError
        with pytest.raises(VectorStoreError):
            await vm.search_similar(query_embedding=[0.0] * 384, limit=5)


class TestVectorInsert:
    """Tests for knowledge insertion."""

    @pytest.mark.asyncio
    async def test_insert_valid_knowledge(self):
        """Happy path: Insert valid knowledge."""
        # Mock the session
        vm = VectorMemory(connection_string="postgresql+asyncpg://localhost/test")

        embedding = np.random.rand(384).tolist()

        with patch.object(vm, "async_session") as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Mock refresh and commit
            mock_session_instance.add = lambda x: setattr(x, "id", 1)
            mock_session_instance.commit = AsyncMock()
            mock_session_instance.refresh = AsyncMock()

            knowledge_id = await vm.insert(
                content="Momentum strategy for trending markets",
                embedding=embedding,
                category="playbook",
                asset="BTC/USDT",
            )

            # Should return an ID
            assert knowledge_id == 1

    @pytest.mark.asyncio
    async def test_insert_wrong_dimension(self):
        """Embedding dimension mismatch should fail."""
        vm = VectorMemory(
            connection_string="postgresql+asyncpg://localhost/test", embedding_dim=384
        )

        # Wrong dimension
        with pytest.raises(VectorStoreError, match="dimension mismatch"):
            await vm.insert(
                content="Test", embedding=[0.0] * 128, category="playbook"  # Wrong size
            )


class TestSimilaritySearch:
    """Tests for similarity search."""

    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        """Happy path: Search with category and asset filters."""
        vm = VectorMemory(connection_string="postgresql+asyncpg://localhost/test")

        query_embedding = np.random.rand(384).tolist()

        with patch.object(vm, "async_session") as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Mock execute result - properly structured
            class MockRow:
                def __init__(self):
                    self.id = 1
                    self.content = "Strategy A"
                    self.category = "playbook"
                    self.asset = "BTC/USDT"
                    self.distance = 0.15

            mock_result = AsyncMock()
            mock_result.all = lambda: [MockRow()]

            async def mock_execute(*args, **kwargs):
                return mock_result

            mock_session_instance.execute = mock_execute

            results = await vm.search_similar(
                query_embedding=query_embedding, limit=5, category="playbook", asset="BTC/USDT"
            )

            assert len(results) == 1
            assert results[0]["content"] == "Strategy A"
            assert results[0]["distance"] == 0.15

    @pytest.mark.asyncio
    async def test_search_database_connection_lost(self):
        """Systemic: Database connection lost during search."""
        vm = VectorMemory(connection_string="postgresql+asyncpg://bad:9999/db")

        query_embedding = [0.0] * 384

        # Should handle gracefully
        with pytest.raises(VectorStoreError):
            await vm.search_similar(query_embedding, limit=5)

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        """Happy path: Search returns no results."""
        vm = VectorMemory(connection_string="postgresql+asyncpg://localhost/test")

        query_embedding = np.random.rand(384).tolist()

        with patch.object(vm, "async_session") as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Mock empty result
            mock_result = AsyncMock()
            mock_result.all = lambda: []

            async def mock_execute(*args, **kwargs):
                return mock_result

            mock_session_instance.execute = mock_execute

            results = await vm.search_similar(query_embedding=query_embedding, limit=5)

            assert results == []


class TestVectorMemoryIntegration:
    """Integration-style tests (would require actual database in real scenario)."""

    @pytest.mark.asyncio
    async def test_insert_then_search_flow(self):
        """Simulate insert -> search flow with mocks."""
        vm = VectorMemory(connection_string="postgresql+asyncpg://localhost/test")

        embedding = np.random.rand(384).tolist()

        with patch.object(vm, "async_session") as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_instance

            # Mock insert
            mock_session_instance.add = lambda x: setattr(x, "id", 42)
            mock_session_instance.commit = AsyncMock()
            mock_session_instance.refresh = AsyncMock()

            knowledge_id = await vm.insert(
                content="Bull market playbook",
                embedding=embedding,
                category="playbook",
                asset="BTC/USDT",
            )

            assert knowledge_id == 42

            # Mock search
            class MockRow:
                def __init__(self):
                    self.id = 42
                    self.content = "Bull market playbook"
                    self.category = "playbook"
                    self.asset = "BTC/USDT"
                    self.distance = 0.0

            mock_result = AsyncMock()
            mock_result.all = lambda: [MockRow()]

            async def mock_execute(*args, **kwargs):
                return mock_result

            mock_session_instance.execute = mock_execute

            results = await vm.search_similar(
                query_embedding=embedding, limit=1, category="playbook"
            )

            # Should find inserted knowledge
            assert len(results) == 1
            assert results[0]["id"] == 42
