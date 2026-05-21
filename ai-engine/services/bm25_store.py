"""BM25 keyword search store backed by PostgreSQL.

Stores raw chunk text alongside the Pinecone vector index so we can run
lexical (BM25) search at query time — critical for matching exact numbers,
model names, acronyms, and technical terms that semantic embeddings miss.
"""

import re
from typing import Optional

# pyrefly: ignore [missing-import]
from rank_bm25 import BM25Okapi

from app.db import get_connection


# ---------------------------------------------------------------------------
# Persistence (PostgreSQL)
# ---------------------------------------------------------------------------

def store_chunks(
    chunks: list[str],
    doc_id: str,
    filename: str,
    user_id: str,
) -> None:
    """Insert chunk texts into the document_chunks table."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for i, text in enumerate(chunks):
                cur.execute(
                    """
                    INSERT INTO document_chunks (user_id, doc_id, chunk_index, chunk_text, filename)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, doc_id, chunk_index) DO UPDATE
                        SET chunk_text = EXCLUDED.chunk_text,
                            filename   = EXCLUDED.filename
                    """,
                    (user_id, doc_id, i, text, filename),
                )
        conn.commit()
        print(f"BM25 store: saved {len(chunks)} chunks for doc {doc_id}")
    except Exception as exc:
        conn.rollback()
        print(f"BM25 store: insert failed — {exc}")


def delete_chunks(doc_id: str, user_id: str) -> int:
    """Remove all chunks for a document. Returns count deleted."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM document_chunks WHERE user_id = %s AND doc_id = %s",
                (user_id, doc_id),
            )
            deleted = cur.rowcount
        conn.commit()
        return deleted
    except Exception as exc:
        conn.rollback()
        print(f"BM25 store: delete failed — {exc}")
        return 0


def _load_user_chunks(user_id: str) -> list[dict]:
    """Load all chunks belonging to a user."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT doc_id, chunk_index, chunk_text, filename
            FROM document_chunks
            WHERE user_id = %s
            ORDER BY doc_id, chunk_index
            """,
            (user_id,),
        )
        rows = cur.fetchall()
    return [
        {"doc_id": r[0], "chunk_index": r[1], "text": r[2], "filename": r[3]}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Tokenisation helpers
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-zA-Z0-9][\w\-\.]*[a-zA-Z0-9]|[a-zA-Z0-9]")


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokenizer that preserves acronyms, numbers, and hyphenated terms."""
    return _TOKEN_RE.findall(text.lower())


# ---------------------------------------------------------------------------
# BM25 search
# ---------------------------------------------------------------------------

def bm25_search(
    query: str,
    user_id: str,
    top_k: int = 10,
) -> list[dict]:
    """Run BM25 over the user's stored chunks and return the top-K results.

    Each result is a dict with keys: text, doc_id, chunk_index, filename, score.
    """
    chunks = _load_user_chunks(user_id)
    if not chunks:
        return []

    corpus = [_tokenize(c["text"]) for c in chunks]
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query_tokens)

    scored = sorted(
        zip(scores, chunks),
        key=lambda x: x[0],
        reverse=True,
    )

    results = []
    for score, chunk in scored[:top_k]:
        if score <= 0:
            break
        results.append({
            "text": chunk["text"],
            "doc_id": chunk["doc_id"],
            "chunk_index": chunk["chunk_index"],
            "filename": chunk["filename"],
            "score": float(score),
        })
    return results
