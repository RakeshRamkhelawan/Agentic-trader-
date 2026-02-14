"""
Tenant-Aware ChromaDB Client.

Wraps ChromaDB to enforce multi-tenant collection isolation
by prefixing collection names with tenant_id.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import chromadb, but allow graceful fallback
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None


class TenantIsolationError(Exception):
    """Raised when tenant isolation cannot be enforced."""

    pass


class TenantAwareChromaClient:
    """
    ChromaDB client with automatic tenant isolation.

    Features:
    - Prefixes all collection names with tenant_id
    - Prevents cross-tenant collection access
    - Provides tenant-scoped operations
    """

    def __init__(
        self,
        tenant_id: str,
        host: str = "localhost",
        port: int = 8000,
        persist_directory: Optional[str] = None,
    ):
        """
        Initialize tenant-aware ChromaDB client.

        Args:
            tenant_id: Tenant identifier for collection prefixing
            host: ChromaDB server host
            port: ChromaDB server port
            persist_directory: Optional local persistence path
        """
        if not tenant_id:
            raise TenantIsolationError("tenant_id is required")

        self.tenant_id = tenant_id
        self.host = host
        self.port = port
        self.persist_directory = persist_directory
        self._client = None

        self._init_client()

    def _init_client(self) -> None:
        """Initialize ChromaDB client."""
        if not CHROMADB_AVAILABLE:
            logger.warning("chromadb not installed, using mock client")
            return

        try:
            if self.persist_directory:
                # Local persistent client
                self._client = chromadb.PersistentClient(path=self.persist_directory)
            else:
                # HTTP client (server mode)
                self._client = chromadb.HttpClient(host=self.host, port=self.port)
            logger.info(f"ChromaDB client initialized for tenant: {self.tenant_id}")
        except Exception as e:
            logger.warning(f"Failed to connect to ChromaDB: {e}")
            self._client = None

    def get_prefixed_name(self, collection_name: str) -> str:
        """
        Get tenant-prefixed collection name.

        Args:
            collection_name: Base collection name

        Returns:
            Prefixed collection name: "{tenant_id}_{collection_name}"
        """
        # Sanitize tenant_id for use in collection name
        safe_tenant = self.tenant_id.replace("-", "_").replace(".", "_")
        return f"{safe_tenant}_{collection_name}"

    def get_collection(self, name: str, create_if_missing: bool = True):
        """
        Get a tenant-isolated collection.

        Args:
            name: Base collection name (will be prefixed with tenant_id)
            create_if_missing: Create collection if it doesn't exist

        Returns:
            ChromaDB collection or None
        """
        prefixed_name = self.get_prefixed_name(name)

        if not self._client:
            logger.warning("ChromaDB not available, returning mock collection")
            return MockCollection(prefixed_name)

        try:
            if create_if_missing:
                return self._client.get_or_create_collection(name=prefixed_name)
            else:
                return self._client.get_collection(name=prefixed_name)
        except Exception as e:
            logger.error(f"Failed to get collection {prefixed_name}: {e}")
            return None

    def list_collections(self) -> List[str]:
        """
        List all collections for this tenant.

        Returns:
            List of collection names (without tenant prefix)
        """
        if not self._client:
            return []

        try:
            all_collections = self._client.list_collections()
            prefix = self.get_prefixed_name("")

            tenant_collections = []
            for col in all_collections:
                col_name = col.name if hasattr(col, "name") else str(col)
                if col_name.startswith(prefix):
                    # Strip tenant prefix
                    base_name = col_name[len(prefix) :]
                    tenant_collections.append(base_name)

            return tenant_collections
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    def delete_collection(self, name: str) -> bool:
        """
        Delete a tenant-isolated collection.

        Args:
            name: Base collection name

        Returns:
            True if deleted successfully
        """
        prefixed_name = self.get_prefixed_name(name)

        if not self._client:
            return False

        try:
            self._client.delete_collection(name=prefixed_name)
            logger.info(f"Deleted collection: {prefixed_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {prefixed_name}: {e}")
            return False


class MockCollection:
    """Mock collection for when ChromaDB is not available."""

    def __init__(self, name: str):
        self.name = name
        self._documents = []
        self._metadatas = []
        self._ids = []

    def add(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """Add documents to mock collection."""
        self._documents.extend(documents)
        if metadatas:
            self._metadatas.extend(metadatas)
        if ids:
            self._ids.extend(ids)

    def query(self, query_texts: List[str], n_results: int = 10) -> Dict[str, Any]:
        """Query mock collection."""
        return {
            "documents": [self._documents[:n_results]],
            "metadatas": [self._metadatas[:n_results]],
            "distances": [[0.0] * min(n_results, len(self._documents))],
        }

    def count(self) -> int:
        """Return document count."""
        return len(self._documents)
