from services.ingest import store_text

print("Seeding data...")
try:
    store_text("Pinecone is a vector database used for semantic search", "1")
    store_text("RAG helps AI use external knowledge instead of guessing", "2")
    store_text("LangGraph enables multi-agent workflows", "3")
    print("Done! Data seeded successfully.")
except Exception as e:
    print(f"Error seeding data: {e}")
