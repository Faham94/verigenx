"""
SpecMind: ChromaDB Embedder
Stores and retrieves document chunks using ChromaDB PersistentClient.

Fixes applied:
  - Bug #4: Was using ephemeral Client() — now uses PersistentClient(CHROMADB_PATH)
  - Bug #5: Was expecting "id" key — now reads "chunk_index" from chunker output
"""
import os
from typing import List, Dict, Optional
from VeriGenX.config import CHROMADB_PATH


class Embedder:

    def __init__(self, collection_name: str = "verigenx_specs"):
        self.collection_name = collection_name
        self._client     = None
        self._collection = None
        self._try_init()

    # ------------------------------------------------------------------ #
    #  Initialisation                                                       #
    # ------------------------------------------------------------------ #
    def _try_init(self):
        """
        Bug #4 fix: Use PersistentClient with CHROMADB_PATH so embeddings
        survive between runs. Falls back gracefully if ChromaDB unavailable.
        """
        try:
            import chromadb
            os.makedirs(CHROMADB_PATH, exist_ok=True)
            self._client     = chromadb.PersistentClient(path=CHROMADB_PATH)   # FIXED
            self._collection = self._client.get_or_create_collection(
                self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            print(f"Warning: ChromaDB not available: {e}")

    # ------------------------------------------------------------------ #
    #  Public API                                                           #
    # ------------------------------------------------------------------ #
    def add(self, chunks: List[Dict]) -> bool:
        """
        Add chunks to ChromaDB collection.

        Bug #5 fix: chunker produces "chunk_index", not "id".
        Now reads "chunk_index" with fallback to index position.
        """
        if self._collection is None:
            print("Warning: ChromaDB not initialised — skipping embed")
            return False
        try:
            ids  = [str(c.get("chunk_index", i)) for i, c in enumerate(chunks)]  # FIXED
            docs = [c["text"] for c in chunks]
            metas = [
                {k: str(v) for k, v in c.get("metadata", {}).items()}
                for c in chunks
            ]
            # ChromaDB add — avoid duplicates by using upsert pattern
            existing_ids = set(self._collection.get(ids=ids)["ids"])
            new_chunks   = [
                (i, d, m) for i, d, m in zip(ids, docs, metas)
                if i not in existing_ids
            ]
            if new_chunks:
                n_ids, n_docs, n_metas = zip(*new_chunks)
                self._collection.add(
                    documents=list(n_docs),
                    ids=list(n_ids),
                    metadatas=list(n_metas),
                )
            return True
        except Exception as e:
            print(f"Embed add failed: {e}")
            return False

    def search(self, query: str, n_results: int = 5) -> List[str]:
        """Semantic similarity search — returns list of matching text chunks."""
        if self._collection is None:
            return []
        try:
            count = self._collection.count()
            if count == 0:
                return []
            n_results = min(n_results, count)
            results   = self._collection.query(
                query_texts=[query],
                n_results=n_results,
            )
            return results.get("documents", [[]])[0]
        except Exception as e:
            print(f"Embed search failed: {e}")
            return []

    def count(self) -> int:
        """Return number of stored chunks."""
        if self._collection is None:
            return 0
        try:
            return self._collection.count()
        except Exception:
            return 0

    def delete_collection(self) -> None:
        """Delete the ChromaDB collection."""
        if self._client:
            try:
                self._client.delete_collection(self.collection_name)
            except Exception as e:
                print(f"Delete failed: {e}")

    def is_ready(self) -> bool:
        """True if ChromaDB is initialised and the collection exists."""
        return self._collection is not None
