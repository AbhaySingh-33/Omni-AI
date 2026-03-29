from app.pinecone_client import index
from app.embeddings import embeddings
from pypdf import PdfReader
import pdfplumber
import os
import hashlib

from services.text_chunker import chunk_text
from services.kg import ingest_document_text


def store_text(text, doc_id, filename="unknown", user_id="default_user"):
    chunks = chunk_text(text)
    
    # Batch embed all chunks at once - much faster!
    print(f"Embedding {len(chunks)} chunks for doc {doc_id}...")
    try:
        all_vectors = embeddings.embed_documents(chunks)
    except Exception as e:
        print(f"Error embedding documents: {e}")
        return None

    vectors = []
    for i, (chunk, vector) in enumerate(zip(chunks, all_vectors)):
        chunk_id = f"{user_id}_{doc_id}_chunk_{i}"
        vectors.append({
            "id": chunk_id,
            "values": vector,
            "metadata": {"text": chunk, "doc_id": doc_id, "chunk": i, "filename": filename, "user_id": user_id}
        })

    # Upsert in batches of 100 (Pinecone limit)
    for i in range(0, len(vectors), 100):
        index.upsert(vectors[i:i + 100])

    print(f"Stored {len(chunks)} chunks for doc: {doc_id}")
    return doc_id


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


def store_pdf(file_path, filename=None, user_id="default_user"):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None

    full_text = _extract_text(file_path)
    if not full_text:
        print(f"Could not extract any text from: {file_path}")
        return None

    doc_id = hashlib.md5(open(file_path, "rb").read()).hexdigest()
    fname = filename or os.path.basename(file_path)
    store_text(full_text, doc_id, fname, user_id)

    try:
        ingest_document_text(full_text, doc_id, fname, user_id)
    except Exception as exc:
        print(f"KG ingest skipped: {exc}")

    print(f"Ingested PDF: {file_path}")
    return doc_id
