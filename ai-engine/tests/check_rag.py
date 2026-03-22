import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.pinecone_client import index
from services.retriever import retrieve_context

# Check vector count
stats = index.describe_index_stats()
count = stats['total_vector_count']
print(f"Vectors in Pinecone: {count}")

if count == 0:
    print("ERROR: No vectors found — ingest may have failed silently")
    sys.exit(1)

# Test retrieval with raw score
from app.embeddings import embeddings
query = "what is this document about"
vector = embeddings.embed_query(query)
results = index.query(vector=vector, top_k=3, include_metadata=True)

print(f"\nTop matches for: '{query}'")
for m in results.get("matches", []):
    print(f"  score={m['score']:.4f} | text={m['metadata']['text'][:100]}")

# Test with MIN_SCORE filter
context = retrieve_context(query)
print(f"\nretrieve_context result: {'FOUND' if context else 'NONE (below MIN_SCORE threshold)'}")
if context:
    print(context[:300])
