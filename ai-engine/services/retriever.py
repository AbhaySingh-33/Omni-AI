from app.pinecone_client import index
from app.embeddings import embeddings

def retrieve_context(query):
    query_vector = embeddings.embed_query(query)

    results = index.query(
        vector=query_vector,
        top_k=3,
        include_metadata=True
    )

    matches = results.get("matches", [])

    if not matches:
        return "No relevant context found."

    texts = [match["metadata"]["text"] for match in matches]

    return "\n".join(texts)