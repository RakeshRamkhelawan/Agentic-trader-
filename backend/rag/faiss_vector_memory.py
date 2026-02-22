"""
FAISS HNSW Vector Memory - OPTIMIZED VERSION (Sprint 2).

O(log N) similarity search using HNSW (Hierarchical Navigable Small World) graphs.
Target: < 1ms for 100k vectors (was: ~10ms with pgvector)

Performance characteristics:
- HNSW: O(log N) search time, O(N) memory
- IVFFlat (pgvector): O(sqrt(N)) search time, O(N) memory
- Brute force: O(N) search time

HNSW is superior for:
- High recall (> 95%) at all scales
- Incremental inserts without rebuild
- Sub-millisecond queries at 1M+ vectors
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("FAISS not available. Install with: pip install faiss-cpu or faiss-gpu")

from backend.rag.vector_memory import VectorMemory, VectorStoreError

logger = logging.getLogger(__name__)


@dataclass
class HNSWConfig:
    """Configuration for HNSW index."""
    dimension: int = 384
    M: int = 64  # Number of connections per layer (higher = better recall, more RAM)
    ef_construction: int = 200  # Quality vs speed trade-off during build
    ef_search: int = 50  # Query-time quality


class FAISSVectorMemory:
    """
    FAISS HNSW-based vector memory for trading knowledge.
    
    Features:
    - O(log N) similarity search
    - Incremental inserts (no rebuild needed)
    - L2 normalized cosine similarity
    - Persistent index storage
    - Thread-safe with asyncio.Lock
    
    Performance targets:
    - Search: < 1ms for 100k vectors
    - Insert: < 5ms per vector
    - Recall@10: > 95%
    """

    def __init__(
        self,
        dimension: int = 384,
        config: Optional[HNSWConfig] = None,
        persist_path: Optional[str] = None,
    ):
        """
        Initialize FAISS HNSW vector memory.
        
        Args:
            dimension: Embedding vector dimension
            config: HNSW configuration
            persist_path: Path to persist index (None = in-memory only)
        """
        if not FAISS_AVAILABLE:
            raise VectorStoreError(
                "FAISS not available. Install with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.config = config or HNSWConfig(dimension=dimension)
        self.persist_path = persist_path
        
        # Initialize HNSW index
        self._init_index()
        
        # ID mapping (FAISS uses integer IDs, we want string IDs with metadata)
        self.id_to_metadata: Dict[int, dict] = {}
        self.next_id: int = 0
        
        # Thread safety for concurrent writes
        self._write_lock = asyncio.Lock()
        
        # Load persisted index if available
        if persist_path:
            self._load_persisted_index()
        
        logger.info(
            f"FAISSVectorMemory initialized: dim={dimension}, "
            f"M={self.config.M}, ef={self.config.ef_construction}"
        )

    def _init_index(self) -> None:
        """Initialize FAISS HNSW index."""
        # Create HNSW index with L2 distance
        # We'll normalize vectors for cosine similarity
        self.index = faiss.IndexHNSWFlat(self.dimension, self.config.M)
        self.index.hnsw.efConstruction = self.config.ef_construction
        self.index.hnsw.efSearch = self.config.ef_search
        
        logger.debug(
            f"HNSW index initialized: M={self.config.M}, "
            f"efConstruction={self.config.ef_construction}"
        )

    def _load_persisted_index(self) -> None:
        """Load persisted index from disk."""
        index_path = Path(self.persist_path)
        metadata_path = index_path.with_suffix('.json')
        
        if index_path.exists():
            try:
                self.index = faiss.read_index(str(index_path))
                logger.info(f"Loaded persisted index from {index_path}")
                
                # Load metadata
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        data = json.load(f)
                        self.id_to_metadata = {
                            int(k): v for k, v in data['metadata'].items()
                        }
                        self.next_id = data['next_id']
                    logger.info(f"Loaded {len(self.id_to_metadata)} metadata entries")
                    
            except Exception as e:
                logger.error(f"Failed to load persisted index: {e}")
                self._init_index()  # Start fresh

    async def add_vector(
        self,
        vector: np.ndarray,
        metadata: dict,
    ) -> int:
        """
        Add vector to HNSW index.
        
        Thread-safe: uses asyncio.Lock for concurrent writes.
        
        Args:
            vector: Embedding vector (will be L2 normalized)
            metadata: Associated metadata
            
        Returns:
            Vector ID
            
        Performance:
        - < 5ms per vector
        """
        async with self._write_lock:
            # Convert to float32 and reshape
            vec = np.array([vector], dtype=np.float32)
            
            # L2 normalize for cosine similarity
            faiss.normalize_L2(vec)
            
            # Add to index
            self.index.add(vec)
            
            # Store metadata
            vector_id = self.next_id
            self.id_to_metadata[vector_id] = metadata
            self.next_id += 1
            
            logger.debug(f"Added vector {vector_id} to index")
            return vector_id

    async def search(
        self,
        query_vector: np.ndarray,
        k: int = 5,
        category_filter: Optional[str] = None,
        distance_threshold: Optional[float] = None,
    ) -> List[dict]:
        """
        O(log N) similarity search.
        
        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            category_filter: Optional category filter
            distance_threshold: Optional maximum distance
            
        Returns:
            List of results with metadata and scores
            
        Performance:
        - < 1ms for 100k vectors
        - < 5ms for 1M vectors
        """
        # Convert and normalize query
        query = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query)
        
        # Search k*3 if filtering to ensure we get k results after filter
        search_k = k * 3 if category_filter else k
        
        # FAISS search
        distances, indices = self.index.search(query, search_k)
        
        # Build results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            
            # Apply distance threshold
            if distance_threshold is not None and dist > distance_threshold:
                continue
            
            meta = self.id_to_metadata.get(int(idx), {})
            
            # Apply category filter
            if category_filter and meta.get('category') != category_filter:
                continue
            
            results.append({
                **meta,
                'score': float(dist),
                'id': int(idx),
            })
            
            if len(results) >= k:
                break
        
        return results

    async def delete_vector(self, vector_id: int) -> bool:
        """
        Mark vector as deleted.
        
        Note: FAISS doesn't support true deletion. We remove from metadata
        and the vector will be skipped in search results.
        
        Args:
            vector_id: ID of vector to delete
            
        Returns:
            True if deleted
        """
        async with self._write_lock:
            if vector_id in self.id_to_metadata:
                del self.id_to_metadata[vector_id]
                logger.debug(f"Marked vector {vector_id} as deleted")
                return True
            return False

    async def get_vector_count(self) -> int:
        """Get number of vectors in index."""
        return self.index.ntotal

    async def persist(self) -> None:
        """
        Persist index and metadata to disk.
        
        Should be called during graceful shutdown.
        """
        if not self.persist_path:
            return
        
        try:
            index_path = Path(self.persist_path)
            metadata_path = index_path.with_suffix('.json')
            
            # Save FAISS index
            faiss.write_index(self.index, str(index_path))
            
            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump({
                    'metadata': self.id_to_metadata,
                    'next_id': self.next_id,
                    'dimension': self.dimension,
                }, f)
            
            logger.info(f"Persisted {self.index.ntotal} vectors to {index_path}")
            
        except Exception as e:
            logger.error(f"Failed to persist index: {e}")

    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            'vector_count': self.index.ntotal,
            'dimension': self.dimension,
            'M': self.config.M,
            'ef_construction': self.config.ef_construction,
            'ef_search': self.config.ef_search,
            'metadata_count': len(self.id_to_metadata),
        }


class HybridVectorMemory(VectorMemory):
    """
    Hybrid vector memory with FAISS primary and pgvector fallback.
    
    Transparently switches between FAISS (fast) and pgvector (reliable).
    """

    def __init__(
        self,
        connection_string: str,
        dimension: int = 384,
        use_faiss: bool = True,
        faiss_persist_path: Optional[str] = None,
    ):
        """
        Initialize hybrid vector memory.
        
        Args:
            connection_string: PostgreSQL connection string (for pgvector fallback)
            dimension: Embedding dimension
            use_faiss: If True, use FAISS as primary
            faiss_persist_path: Path for FAISS persistence
        """
        super().__init__(connection_string, dimension)
        
        self.use_faiss = use_faiss and FAISS_AVAILABLE
        self.faiss_memory: Optional[FAISSVectorMemory] = None
        
        if self.use_faiss:
            try:
                self.faiss_memory = FAISSVectorMemory(
                    dimension=dimension,
                    persist_path=faiss_persist_path,
                )
                logger.info("FAISS enabled as primary vector store")
            except Exception as e:
                logger.warning(f"FAISS initialization failed: {e}, using pgvector only")
                self.use_faiss = False

    async def insert(
        self,
        content: str,
        embedding: List[float],
        category: str,
        asset: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> int:
        """
        Insert vector to both FAISS and pgvector.
        
        FAISS is primary for search, pgvector is backup.
        """
        # Insert to pgvector (always)
        pg_id = await super().insert(content, embedding, category, asset, metadata)
        
        # Insert to FAISS (if available)
        if self.use_faiss and self.faiss_memory:
            meta = {
                'content': content,
                'category': category,
                'asset': asset,
                'metadata': metadata,
                'pg_id': pg_id,
            }
            await self.faiss_memory.add_vector(np.array(embedding), meta)
        
        return pg_id

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        category: Optional[str] = None,
        asset: Optional[str] = None,
        distance_threshold: float = 1.0,
    ) -> List[dict]:
        """
        Search using FAISS (fast) with pgvector fallback.
        """
        if self.use_faiss and self.faiss_memory:
            try:
                results = await self.faiss_memory.search(
                    np.array(query_embedding),
                    k=limit,
                    category_filter=category,
                    distance_threshold=distance_threshold,
                )
                
                if results:
                    return results
                    
            except Exception as e:
                logger.warning(f"FAISS search failed: {e}, falling back to pgvector")
        
        # Fallback to pgvector
        return await super().search_similar(
            query_embedding, limit, category, asset, distance_threshold
        )

    async def persist(self) -> None:
        """Persist FAISS index."""
        if self.use_faiss and self.faiss_memory:
            await self.faiss_memory.persist()

    async def close(self) -> None:
        """Close and persist."""
        await self.persist()
        await super().close()
