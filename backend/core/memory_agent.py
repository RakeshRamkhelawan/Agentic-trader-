import logging
import uuid
from typing import Any, Dict, List, Optional

try:
    import chromadb
except ImportError:
    chromadb = None

from threading import Lock

from backend.core.auth.context import get_current_tenant_optional
from backend.core.config.settings import settings


class MemoryAgent:
    """
    Manages Semantic Memory (RAG) using Vector Database.
    Allows agents to store thoughts and recall similar past experiences.
    """

    def __init__(self, client=None, collection_name: str = "agent_thoughts"):
        if chromadb is None:
            raise ImportError("chromadb not installed")

        self.client = client or chromadb.HttpClient(
            host=settings.CHROMA_HOST, port=settings.CHROMA_PORT
        )

        self.base_collection_name = collection_name
        # Cache collections per tenant: {tenant_id: Collection}
        self._collections: Dict[str, Any] = {}
        self._lock = Lock()

        self.logger = logging.getLogger("MemoryAgent")

    def _get_collection(self) -> Any:
        """
        Get the collection for the current tenant.
        """
        tenant_id = get_current_tenant_optional()

        # If no tenant context, use a default fallback or raise error
        # For now, we use a 'public' or 'system' prefix, or just the base name
        # But for isolation, we should probably default to 'default' tenant if allowed
        if not tenant_id:
            tenant_id = "default"

        collection_name = f"{tenant_id}_{self.base_collection_name}"

        with self._lock:
            if collection_name in self._collections:
                return self._collections[collection_name]

            # Create or Get Collection
            collection = self.client.get_or_create_collection(
                name=collection_name, metadata={"hnsw:space": "cosine"}
            )
            self._collections[collection_name] = collection
            return collection

    def store_thought(self, agent_id: str, text: str, metadata: Optional[Dict] = None):
        """
        Store a reasoning trace in the vector DB.
        """
        if metadata is None:
            metadata = {}

        metadata["agent_id"] = agent_id
        metadata["timestamp"] = str(uuid.uuid1())
        metadata["tenant_id"] = get_current_tenant_optional() or "default"

        collection = self._get_collection()
        collection.add(documents=[text], metadatas=[metadata], ids=[str(uuid.uuid4())])
        self.logger.debug(f"Stored thought for {agent_id}: {text[:50]}...")

    def recall_thoughts(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant past thoughts based on semantic similarity.
        """
        self.logger.debug(f"Recalling thoughts for query: {query[:50]}...")
        collection = self._get_collection()
        results = collection.query(query_texts=[query], n_results=limit)

        parsed_results = []
        if results["documents"]:
            for i in range(len(results["documents"][0])):
                parsed_results.append(
                    {
                        "document": results["documents"][0][i],
                        "metadata": (
                            results["metadatas"][0][i] if results["metadatas"] else {}
                        ),
                        "id": results["ids"][0][i],
                    }
                )
        self.logger.debug(f"Recalled {len(parsed_results)} thoughts.")
        return parsed_results
