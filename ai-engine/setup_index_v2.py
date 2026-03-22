from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
import time

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "omni-ai-v2"

# Check if index exists
if index_name not in pc.list_indexes().names():
    print(f"Creating new index: {index_name} with dimension 3072")
    try:
        pc.create_index(
            name=index_name,
            dimension=3072,  # Matching Gemini Embedding 001
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        print("Index created successfully!")
    except Exception as e:
        print(f"Error creating index: {e}")
else:
    print(f"Index {index_name} already exists.")
