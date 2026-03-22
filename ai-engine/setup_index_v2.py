from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
import time

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "omni-ai-v2"

# Delete old index if it exists (dimension mismatch fix)
if index_name in pc.list_indexes().names():
    print(f"Deleting existing index: {index_name}")
    pc.delete_index(index_name)
    print("Deleted.")

print(f"Creating index: {index_name} with dimension 1024 (Mistral embeddings)")
try:
    pc.create_index(
        name=index_name,
        dimension=1024,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
    print("Index created successfully!")
except Exception as e:
    print(f"Error creating index: {e}")
