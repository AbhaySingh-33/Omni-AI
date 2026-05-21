"""Migration: create the document_chunks table for BM25 keyword search.

Run once at startup via init_document_chunks_table().
"""

from app.db import get_connection


def init_document_chunks_table():
    """Create the document_chunks table if it does not exist."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id          SERIAL PRIMARY KEY,
                    user_id     TEXT NOT NULL,
                    doc_id      TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_text  TEXT NOT NULL,
                    filename    TEXT,
                    created_at  TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, doc_id, chunk_index)
                );
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_user
                ON document_chunks(user_id);
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_doc
                ON document_chunks(user_id, doc_id);
            """)
            conn.commit()
            print("document_chunks table ready")
    except Exception as exc:
        conn.rollback()
        print(f"Warning: document_chunks migration failed: {exc}")
    finally:
        conn.close()
