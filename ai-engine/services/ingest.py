from app.pinecone_client import index
from app.embeddings import embeddings
from pypdf import PdfReader
import pdfplumber
import os
import hashlib

CHUNK_SIZE = 500      # characters per chunk
CHUNK_OVERLAP = 100   # overlap between chunks to preserve context


def _chunk_text(text):
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if c]


def store_text(text, doc_id):
    chunks = _chunk_text(text)
    vectors = []
    for i, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}_chunk_{i}"
        vector = embeddings.embed_query(chunk)
        vectors.append({
            "id": chunk_id,
            "values": vector,
            "metadata": {"text": chunk, "doc_id": doc_id, "chunk": i}
        })

    # Upsert in batches of 100 (Pinecone limit)
    for i in range(0, len(vectors), 100):
        index.upsert(vectors[i:i + 100])

    print(f"Stored {len(chunks)} chunks for doc: {doc_id}")


def _extract_text(file_path):
    # Try pypdf first
    try:
        reader = PdfReader(file_path)
        pages = [p.extract_text() for p in reader.pages if p.extract_text()]
        if pages:
            return "\n".join(pages)
    except Exception:
        pass

    # Fallback to pdfplumber for malformed/compressed PDFs
    try:
        with pdfplumber.open(file_path) as pdf:
            pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
            if pages:
                print("  (used pdfplumber fallback)")
                return "\n".join(pages)
    except Exception as e:
        print(f"pdfplumber also failed: {e}")

    return None


def store_pdf(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    full_text = _extract_text(file_path)
    if not full_text:
        print(f"Could not extract any text from: {file_path}")
        return

    # Stable ID based on file content so re-ingesting the same file is idempotent
    doc_id = hashlib.md5(open(file_path, "rb").read()).hexdigest()

    store_text(full_text, doc_id)
    print(f"Ingested PDF: {file_path}")
