from app.pinecone_client import index
from app.embeddings import embeddings
from pypdf import PdfReader
import os

def store_text(text, id):
    try:
        vector = embeddings.embed_query(text)
        index.upsert([
            {
                "id": str(id),
                "values": vector,
                "metadata": {"text": text}
            }
        ])
        print(f"Stored: {text[:50]}...")
    except Exception as e:
        print(f"Error storing text: {e}")

def store_pdf(file_path):
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
            
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        # Store the extracted text
        # Using filename as ID for simplicity, but could be better
        doc_id = os.path.basename(file_path)
        store_text(text, doc_id)
        print(f"Stored PDF content from: {file_path}")
        
    except Exception as e:
        print(f"Error processing PDF {file_path}: {e}")
