"""Hybrid retriever: BM25 (keyword) + Pinecone (vector) with RRF fusion.

Runs both searches in parallel and merges results using Reciprocal Rank
Fusion so that exact-match terms (numbers, acronyms, model names) get
properly boosted alongside semantically relevant chunks.
"""

import concurrent.futures
from typing import Optional

from app.pinecone_client import index
from app.embeddings import embeddings
from services.bm25_store import bm25_search

# --- Configuration ---------------------------------------------------------
VECTOR_TOP_K = 10
BM25_TOP_K = 10
VECTOR_MIN_SCORE = 0.35
RRF_K = 60          # Standard RRF constant
FINAL_TOP_K = 8     # Chunks returned to the LLM
# ---------------------------------------------------------------------------


def _vector_search(query: str, user_id: str) -> list[dict]:
    """Pinecone semantic vector search."""
    query_vector = embeddings.embed_query(query)
    results = index.query(
        vector=query_vector,
        top_k=VECTOR_TOP_K,
        include_metadata=True,
        filter={"user_id": {"$eq": user_id}},
    )
    matches = []
    for m in results.get("matches", []):
        if m.get("score", 0) < VECTOR_MIN_SCORE:
            continue
        meta = m.get("metadata", {})
        matches.append({
            "text": meta.get("text", ""),
            "doc_id": meta.get("doc_id", ""),
            "chunk_index": meta.get("chunk", -1),
            "filename": meta.get("filename", ""),
            "score": m["score"],
        })
    return matches


def _rrf_fuse(
    vector_results: list[dict],
    bm25_results: list[dict],
    k: int = RRF_K,
) -> list[dict]:
    """Reciprocal Rank Fusion across two ranked lists.

    score(doc) = Σ  1 / (k + rank_i)   for each list i that contains doc.
    """
    scores: dict[str, float] = {}
    chunk_map: dict[str, dict] = {}

    def _key(item: dict) -> str:
        return f"{item['doc_id']}::{item['chunk_index']}"

    for rank, item in enumerate(vector_results):
        uid = _key(item)
        scores[uid] = scores.get(uid, 0.0) + 1.0 / (k + rank + 1)
        chunk_map[uid] = item

    for rank, item in enumerate(bm25_results):
        uid = _key(item)
        scores[uid] = scores.get(uid, 0.0) + 1.0 / (k + rank + 1)
        if uid not in chunk_map:
            chunk_map[uid] = item

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    results = []
    for uid, rrf_score in ranked:
        entry = chunk_map[uid].copy()
        entry["rrf_score"] = rrf_score
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def hybrid_retrieve(
    query: str,
    user_id: str,
    top_k: int = FINAL_TOP_K,
) -> Optional[str]:
    """Run hybrid BM25 + vector search and return fused context string.

    Returns None when no relevant chunks are found.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        vec_future = pool.submit(_vector_search, query, user_id)
        bm25_future = pool.submit(bm25_search, query, user_id, BM25_TOP_K)

        try:
            vector_results = vec_future.result(timeout=5.0)
        except Exception:
            vector_results = []

        try:
            bm25_results = bm25_future.result(timeout=3.0)
        except Exception:
            bm25_results = []

    if not vector_results and not bm25_results:
        return None

    fused = _rrf_fuse(vector_results, bm25_results)[:top_k]

    # Build a context string with source attribution per chunk
    parts = []
    for i, chunk in enumerate(fused, 1):
        header = f"[Chunk {i} | {chunk.get('filename', 'unknown')}]"
        parts.append(f"{header}\n{chunk['text']}")

    return "\n\n---\n\n".join(parts)


# Backward-compatible alias so existing callers still work
def retrieve_context(query: str, user_id: str = "default_user") -> Optional[str]:
    """Drop-in replacement for the old vector-only retriever."""
    return hybrid_retrieve(query, user_id)
