from app.pinecone_client import index
from app.embeddings import embeddings

MIN_SCORE = 0.45

def retrieve_context(query, user_id="default_user"):
    query_vector = embeddings.embed_query(query)

    results = index.query(
        vector=query_vector,
        top_k=5,
        include_metadata=True,
        filter={"user_id": {"$eq": user_id}}
    )

    matches = [m for m in results.get("matches", []) if m.get("score", 0) >= MIN_SCORE]

    if not matches:
        return None

    texts = [m["metadata"]["text"] for m in matches]
    return "\n---\n".join(texts)
