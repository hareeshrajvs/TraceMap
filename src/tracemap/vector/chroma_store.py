"""ChromaDB persistent vector store for requirement document semantic search."""

from __future__ import annotations

from tracemap.config import ensure_data_dirs, get_settings

_chroma_client = None
_collection = None
_embedding_fn = None
_fallback_chunks: list[dict] = []
_chroma_available: bool | None = None


def _is_chroma_available() -> bool:
    global _chroma_available
    if _chroma_available is None:
        try:
            import chromadb  # noqa: F401

            _chroma_available = True
        except ImportError:
            _chroma_available = False
    return _chroma_available


def _get_embedding_function():
    global _embedding_fn
    if _embedding_fn is None:
        from chromadb.utils import embedding_functions

        settings = get_settings()
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )
    return _embedding_fn


def _get_collection():
    global _chroma_client, _collection
    if _collection is None:
        import chromadb

        ensure_data_dirs()
        settings = get_settings()
        _chroma_client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        _collection = _chroma_client.get_or_create_collection(
            name="requirements",
            embedding_function=_get_embedding_function(),
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = end - overlap
    return chunks


def index_document(
    raw_text: str,
    doc_hash: str,
    source_ref: str,
    source_type: str,
) -> int:
    """Chunk and index document text. Falls back to in-memory store if ChromaDB unavailable."""
    chunks = _chunk_text(raw_text)
    if not chunks:
        return 0

    if not _is_chroma_available():
        global _fallback_chunks
        _fallback_chunks = [
            {
                "text": c,
                "metadata": {
                    "source_ref": source_ref,
                    "source_type": source_type,
                    "doc_hash": doc_hash,
                    "chunk_index": i,
                },
            }
            for i, c in enumerate(chunks)
        ]
        return len(chunks)

    collection = _get_collection()
    existing = collection.get(where={"source_ref": source_ref})
    if existing and existing.get("ids"):
        collection.delete(ids=existing["ids"])

    ids = [f"{doc_hash[:12]}-{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "source_ref": source_ref,
            "source_type": source_type,
            "doc_hash": doc_hash,
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]
    collection.add(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)


def search_context(query: str, top_k: int = 5, source_ref: str | None = None) -> list[dict]:
    """Semantic search over indexed chunks."""
    if not _is_chroma_available():
        results = _fallback_chunks
        if source_ref:
            results = [c for c in results if c["metadata"].get("source_ref") == source_ref]
        return results[:top_k]

    collection = _get_collection()
    where = {"source_ref": source_ref} if source_ref else None
    try:
        count = collection.count()
        if count == 0:
            return []
        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, count),
            where=where,
        )
    except Exception:
        results = collection.query(query_texts=[query], n_results=top_k)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    return [
        {"text": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]


def get_chunk_count() -> int:
    if not _is_chroma_available():
        return len(_fallback_chunks)
    try:
        return _get_collection().count()
    except Exception:
        return 0
