"""
CineMatch — ChromaDB Vector Database Module

Handles creation and querying of the ChromaDB collection that stores
CLIP image embeddings alongside scene metadata.
"""

import chromadb
from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parent.parent / "data" / "chromadb_store")
COLLECTION_NAME = "film_scenes"

_client = None
_collection = None


def get_collection():
    """Get or create the ChromaDB collection for film scene embeddings."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=DB_PATH)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_scene(scene_id: str, embedding: list[float], metadata: dict):
    """Add a scene embedding and its metadata to the collection."""
    collection = get_collection()
    collection.upsert(
        ids=[scene_id],
        embeddings=[embedding],
        metadatas=[metadata],
    )


def query_scenes(query_embedding: list[float], n_results: int = 5):
    """
    Query the collection with a text embedding and return the top matches.

    ChromaDB with cosine space returns distances in [0, 2] where 0 = identical.
    We convert to a similarity score in [0, 1] as: similarity = 1 - (distance / 2).
    """
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["metadatas", "distances"],
    )
    return results


def collection_count() -> int:
    """Return the number of items currently in the collection."""
    collection = get_collection()
    return collection.count()


def clear_collection():
    """Delete and recreate the collection."""
    global _client, _collection
    client = chromadb.PersistentClient(path=DB_PATH)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    _client = None
    _collection = None
