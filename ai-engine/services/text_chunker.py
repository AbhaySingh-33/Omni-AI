"""Sentence-boundary-aware text chunker for RAG ingestion.

Uses LangChain's RecursiveCharacterTextSplitter so chunks never break
mid-sentence — keeping numbers, acronyms, and model names intact.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", "; ", ", ", " ", ""],
    keep_separator=True,
    strip_whitespace=True,
)


def chunk_text(text: str) -> list[str]:
    """Split *text* into overlapping chunks at sentence boundaries."""
    if not text or not text.strip():
        return []
    chunks = _splitter.split_text(text)
    return [c for c in chunks if c.strip()]
