"""
SpecMind: ChromaDB Embedder
Stores and retrieves document chunks using ChromaDB
"""
from typing import List, Dict, Any, Optional

class Embedder:
    def __init__(self, collection_name: str = "verigenx_specs"):
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._try_init()
    
    def _try_init(self):
        """Initialize ChromaDB client (graceful fallback if not available)"""
        try:
            import chromadb
            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(self.collection_name)
        except Exception as e:
            print(f"Warning: ChromaDB not available: {e}")
    
    def add(self, chunks: List[Dict]) -> bool:
        """Add chunks to ChromaDB collection"""
        if self._collection is None:
            print("Warning: ChromaDB not initialized, skipping embed")
            return False
        try:
            ids = [str(c["id"]) for c in chunks]
            docs = [c["text"] for c in chunks]
            self._collection.add(documents=docs, ids=ids)
            return True
        except Exception as e:
            print(f"Embed add failed: {e}")
            return False
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar chunks"""
        if self._collection is None:
            return []
        try:
            results = self._collection.query(query_texts=[query], n_results=n_results)
            return results.get("documents", [[]])[0]
        except Exception as e:
            print(f"Embed search failed: {e}")
            return []
    
    def delete_collection(self):
        """Delete the collection"""
        if self._client:
            try:
                self._client.delete_collection(self.collection_name)
            except Exception as e:
                print(f"Delete failed: {e}")
