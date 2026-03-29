from services.ingest import store_text
from services.kg import ingest_document_text
import sys
import traceback

print("Seeding data...")

documents = [
    {
        "id": "1", 
        "text": "Pinecone is a vector database managed service designed to handle high-dimensional vectors for semantic search. It allows efficient retrieval of relevant information for Large Language Models (LLMs).", 
        "filename": "pinecone_info.txt"
    },
    {
        "id": "2", 
        "text": "Retrieval-Augmented Generation (RAG) is a technique that enhances LLM generation by retrieving relevant external knowledge. It combines a retriever (like Pinecone) and a generator (like GPT-4 or Mistral).", 
        "filename": "rag_overview.txt"
    },
    {
        "id": "3", 
        "text": "LangGraph is a library for building stateful, multi-actor applications with LLMs. Unlike simple chains, LangGraph allows for cycles and persistence, enabling complex agentic workflows.", 
        "filename": "langgraph_manual.txt"
    },
    {
        "id": "4", 
        "text": "Neo4j is a graph database management system. It stores data as nodes (entities) and relationships (edges). It is particularly useful for building Knowledge Graphs (KG) that capture structured relationships between concepts.", 
        "filename": "neo4j_intro.txt"
    }
]

def run_seed_data():
    try:
        # Use user_id="3" to match the example JWT token in logs
        user_id = "3" 
        for doc in documents:
            print(f"Processing doc {doc['id']} ({doc['filename']})...")
            
            # 1. Store in Vector DB
            try:
                store_text(doc["text"], doc["id"], doc["filename"], user_id)
                print(f"  - Stored in Pinecone.")
            except Exception as e:
                print(f"  - Error storing in Pinecone: {e}")

            # 2. Ingest into Knowledge Graph
            try:
                ingest_document_text(doc["text"], doc["id"], doc["filename"], user_id)
                print(f"  - Ingested into KG.")
            except Exception as e:
                print(f"  - Error ingesting into KG: {e}")
                traceback.print_exc()
        
        print("\nDone! Data seeded successfully (Vector + KG).")

    except Exception as e:
        print(f"Error seeding data: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_seed_data()
