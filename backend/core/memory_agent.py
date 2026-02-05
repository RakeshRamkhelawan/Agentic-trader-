import logging
import uuid
from typing import List, Dict, Any, Optional

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None

from backend.core.config.settings import settings # NIEUW

class MemoryAgent:
    """
    Manages Semantic Memory (RAG) using Vector Database.
    Allows agents to store thoughts and recall similar past experiences.
    """
    
    def __init__(self, client=None, collection_name: str = "agent_thoughts"):
        if chromadb is None:
            raise ImportError("chromadb not installed")
            
        # Gebruik settings voor host/port
        self.client = client or chromadb.HttpClient(
            host=settings.CHROMA_HOST, 
            port=settings.CHROMA_PORT
        )
        
        # Create or Get Collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.logger = logging.getLogger("MemoryAgent")


    def store_thought(self, agent_id: str, text: str, metadata: Optional[Dict] = None):
        """
        Store a reasoning trace in the vector DB.
        """
        if metadata is None:
            metadata = {}
            
        metadata['agent_id'] = agent_id
        metadata['timestamp'] = str(uuid.uuid1())
        
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())]
        )
        self.logger.debug(f"Stored thought for {agent_id}: {text[:50]}...")

    def recall_thoughts(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant past thoughts based on semantic similarity.
        """
        self.logger.debug(f"Recalling thoughts for query: {query[:50]}...")
        results = self.collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        parsed_results = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                parsed_results.append({
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'id': results['ids'][0][i]
                })
        self.logger.debug(f"Recalled {len(parsed_results)} thoughts.")
        return parsed_results