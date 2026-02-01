import chromadb
import uuid
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = structlog.get_logger()

class SemanticMemory:
    """
    Manages long-term semantic memory using ChromaDB.
    Stores and retrieves text fragments (context) based on vector similarity.
    """
    
    def __init__(self, persistence_path: str = "./chroma_db", collection_name: str = "jarvis_context"):
        """
        Initialize the memory unit.
        
        Args:
            persistence_path: Path to store the Vector DB files.
            collection_name: Name of the ChromaDB collection to use.
        """
        self.client = chromadb.PersistentClient(path=persistence_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        logger.info("Semantic Memory initialized", collection=collection_name, path=persistence_path)

    def save_context(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save a piece of text to memory.
        
        Args:
            text: The text content to remember.
            metadata: Optional key-value pairs (e.g., {"source": "user_chat", "timestamp": "..."})
            
        Returns:
            The ID of the stored item.
        """
        try:
            doc_id = str(uuid.uuid4())
            if metadata is None:
                metadata = {}
            
            # Ensure timestamp is present
            if "timestamp" not in metadata:
                metadata["timestamp"] = datetime.utcnow().isoformat()
                
            self.collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            logger.info("Context saved", doc_id=doc_id, text_preview=text[:50])
            return doc_id
        except Exception as e:
            logger.error("Failed to save context", error=str(e))
            raise

    def query_context(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a given query.
        
        Args:
            query: The search query.
            n_results: Number of results to return.
            
        Returns:
            List of dicts containing 'text' and 'metadata'.
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Formatter results into a cleaner list
            parsed_results = []
            
            # Chroma returns lists of lists (one list per query)
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    item = {
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else None
                    }
                    parsed_results.append(item)
            
            logger.info("Context queried", query=query, results_found=len(parsed_results))
            return parsed_results
            
        except Exception as e:
            logger.error("Failed to query context", error=str(e))
            return []

    def clear_memory(self):
        """Warning: clear all memories."""
        try:
            self.client.delete_collection(self.collection.name)
            self.collection = self.client.get_or_create_collection(self.collection.name)
            logger.warning("Memory cleared")
        except Exception as e:
            logger.error("Failed to clear memory", error=str(e))
