"""
Vector Memory Storage for Trading Knowledge.

Stores and retrieves strategic knowledge using pgvector embeddings.
Provides similarity search for historical scenarios and strategy playbooks.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Index, Integer, String, Text, select
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()


class VectorStoreError(Exception):
    """Base exception for vector store operations."""

    pass


class TradingKnowledge(Base):
    """
    Trading knowledge with vector embeddings.

    Stores strategy playbooks, macro events, and historical scenarios
    for retrieval during the Orient phase of OODA.
    """

    __tablename__ = "trading_knowledge"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False, comment="Knowledge content")
    embedding = Column(Vector(384), nullable=False, comment="Embedding vector")
    category = Column(
        String(50), nullable=False, comment="Category: playbook, macro_event, scenario"
    )
    asset = Column(String(20), nullable=True, comment="Related asset symbol")
    timestamp = Column(
        DateTime, default=datetime.utcnow, nullable=False, comment="Creation timestamp"
    )
    metadata_json = Column(Text, nullable=True, comment="Additional metadata as JSON")

    __table_args__ = (
        Index("idx_category_asset", "category", "asset"),
        Index("idx_embedding_vector", "embedding", postgresql_using="ivfflat"),
    )


class VectorMemory:
    """
    Async vector memory interface for trading knowledge.

    Provides embedding storage and similarity search using pgvector.
    """

    def __init__(
        self,
        connection_string: str,
        embedding_dim: int = 384,
        pool_size: int = 5,
    ):
        """
        Initialize vector memory.

        Args:
            connection_string: PostgreSQL connection string with asyncpg driver
            embedding_dim: Dimension of embedding vectors (default 384 for all-MiniLM-L6-v2)
            pool_size: Database connection pool size
        """
        self.connection_string = connection_string
        self.embedding_dim = embedding_dim

        try:
            self.engine = create_async_engine(
                connection_string,
                pool_size=pool_size,
                max_overflow=10,
            )
            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        except Exception as e:
            logger.error(f"Failed to initialize vector memory: {e}")
            raise VectorStoreError(f"Initialization failed: {e}") from e

    async def initialize_schema(self):
        """
        Create tables and extensions if they don't exist.

        Requires pgvector extension to be available.
        """
        try:
            async with self.engine.begin() as conn:
                # Enable pgvector extension
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

                # Create tables
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Vector memory schema initialized")
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            raise VectorStoreError(f"Schema init failed: {e}") from e

    async def insert(
        self,
        content: str,
        embedding: List[float],
        category: str,
        asset: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Insert trading knowledge with embedding.

        Args:
            content: Knowledge content text
            embedding: Embedding vector (must match embedding_dim)
            category: Knowledge category (playbook, macro_event, scenario)
            asset: Related asset symbol (optional)
            metadata: Additional metadata dict (optional)

        Returns:
            ID of inserted record

        Raises:
            VectorStoreError: On insertion failure
        """
        if len(embedding) != self.embedding_dim:
            raise VectorStoreError(
                f"Embedding dimension mismatch: expected {self.embedding_dim}, got {len(embedding)}"
            )

        try:
            async with self.async_session() as session:
                import json

                knowledge = TradingKnowledge(
                    content=content,
                    embedding=embedding,
                    category=category,
                    asset=asset,
                    metadata_json=json.dumps(metadata) if metadata else None,
                )

                session.add(knowledge)
                await session.commit()
                await session.refresh(knowledge)

                logger.info(
                    f"Inserted knowledge ID {knowledge.id} (category={category})"
                )
                return knowledge.id

        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise VectorStoreError(f"Insert failed: {e}") from e

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        category: Optional[str] = None,
        asset: Optional[str] = None,
        distance_threshold: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar knowledge using cosine distance.

        Args:
            query_embedding: Query embedding vector
            limit: Maximum results to return
            category: Filter by category (optional)
            asset: Filter by asset (optional)
            distance_threshold: Maximum cosine distance (default 1.0)

        Returns:
            List of dicts with keys: id, content, distance, category, asset

        Raises:
            VectorStoreError: On search failure
        """
        if len(query_embedding) != self.embedding_dim:
            raise VectorStoreError(
                f"Query embedding dimension mismatch: expected {self.embedding_dim}"
            )

        try:
            async with self.async_session() as session:
                # Build query with filters
                stmt = select(
                    TradingKnowledge.id,
                    TradingKnowledge.content,
                    TradingKnowledge.category,
                    TradingKnowledge.asset,
                    TradingKnowledge.embedding.cosine_distance(query_embedding).label(
                        "distance"
                    ),
                )

                if category:
                    stmt = stmt.where(TradingKnowledge.category == category)
                if asset:
                    stmt = stmt.where(TradingKnowledge.asset == asset)

                stmt = stmt.where(
                    TradingKnowledge.embedding.cosine_distance(query_embedding)
                    < distance_threshold
                )
                stmt = stmt.order_by("distance")
                stmt = stmt.limit(limit)

                result = await session.execute(stmt)
                rows = result.all()

                # Log search
                logger.info(
                    f"Vector search: {len(rows)} results "
                    f"(category={category}, asset={asset}, limit={limit})"
                )

                return [
                    {
                        "id": row.id,
                        "content": row.content,
                        "category": row.category,
                        "asset": row.asset,
                        "distance": float(row.distance),
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise VectorStoreError(f"Search failed: {e}") from e

    async def close(self):
        """Close database connections."""
        await self.engine.dispose()
        logger.info("Vector memory connections closed")
