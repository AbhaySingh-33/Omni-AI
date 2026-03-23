from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph.workflow import build_graph
from services.memory import save_chat
from services.ingest import store_pdf
from app.gemini import llm
from app.auth import register_user, login_user, create_token, get_current_user
from datetime import datetime
from app.guardrails.input_guard import validate_input
from app.guardrails.output_guard import validate_output
import tempfile, os, shutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()


# ── Auth schemas ──────────────────────────────────────────────
class AuthRequest(BaseModel):
    email: str
    password: str


class ChatRequest(BaseModel):
    message: str


# ── Auth routes ───────────────────────────────────────────────
@app.post("/auth/register")
def register(req: AuthRequest):
    user_id = register_user(req.email, req.password)
    token = create_token(user_id, req.email)
    return {"token": token, "email": req.email}


@app.post("/auth/login")
def login(req: AuthRequest):
    user_id = login_user(req.email, req.password)
    token = create_token(user_id, req.email)
    return {"token": token, "email": req.email}


# ── Helpers ───────────────────────────────────────────────────
def format_response(user_query: str, raw: str) -> str:
    today = datetime.now().strftime("%A, %B %d, %Y")
    prompt = f"""You are a helpful AI assistant. Today's date is {today}.
A user asked a question and you have the raw answer/data below.
Your job is to present it as a clean, well-structured, human-friendly response.

Rules:
- Be concise and direct
- Use bullet points or numbered lists where appropriate
- If it's weather/search data, summarize the key facts clearly
- If it's a calculation, show the result clearly
- If it's a file listing, format it neatly
- If it's code or terminal output, present it cleanly
- Never mention "tool", "MCP", "raw output", or internal system details
- Respond naturally as if you found this information yourself
- Always use today's date ({today}) when the user asks about the current date

User question: {user_query}

Raw data:
{raw}

Now write a clean, structured response:"""
    result = llm.invoke(prompt)
    return result.content


# ── Protected routes ──────────────────────────────────────────
@app.post("/chat")
async def chat(req: ChatRequest, user=Depends(get_current_user)):
    user_id = user["user_id"]

    is_valid, checked_input = validate_input(req.message)
    if not is_valid:
        return {"response": checked_input}

    result = graph.invoke({
        "messages": [("user", checked_input)],
        "user_id": user_id,
        "iterations": 0
    })
    raw_response = result["messages"][-1].content
    final_response = format_response(req.message, raw_response)
    safe_response = validate_output(final_response)

    save_chat(user_id, checked_input, safe_response)
    return {"response": safe_response}


@app.get("/history")
def get_history(user=Depends(get_current_user)):
    from services.memory import get_history as fetch_history
    rows = fetch_history(user["user_id"], limit=50)
    messages = []
    for msg, resp in rows:
        messages.append({"role": "user", "content": msg})
        messages.append({"role": "assistant", "content": resp})
    return {"messages": messages}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        doc_id = store_pdf(tmp_path, file.filename, user["user_id"])
    finally:
        os.unlink(tmp_path)

    return {"status": "ok", "message": f"'{file.filename}' ingested successfully", "doc_id": doc_id}


@app.get("/documents")
def list_documents(user=Depends(get_current_user)):
    from app.pinecone_client import index
    stats = index.describe_index_stats()
    results = index.query(
        vector=[0.0] * int(stats.get("dimension", 1024)),
        top_k=100,
        include_metadata=True,
        filter={"user_id": {"$eq": user["user_id"]}}
    )
    seen = {}
    for m in results.get("matches", []):
        meta = m.get("metadata", {})
        doc_id = meta.get("doc_id")
        if doc_id and doc_id not in seen:
            seen[doc_id] = {"doc_id": doc_id, "filename": meta.get("filename", doc_id[:8] + "…"), "chunks": 0}
        if doc_id:
            seen[doc_id]["chunks"] += 1
    return {"documents": list(seen.values()), "total_chunks": stats.get("total_vector_count", 0)}


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str, user=Depends(get_current_user)):
    from app.pinecone_client import index
    results = index.query(
        vector=[0.0] * 1024, top_k=1000, include_metadata=False,
        filter={"doc_id": {"$eq": doc_id}, "user_id": {"$eq": user["user_id"]}},
    )
    ids = [m["id"] for m in results.get("matches", [])]
    if not ids:
        raise HTTPException(status_code=404, detail="Document not found")
    for i in range(0, len(ids), 100):
        index.delete(ids=ids[i:i + 100])
    return {"status": "ok", "deleted_chunks": len(ids)}


@app.get("/")
def root():
    return {"status": "ok", "message": "OmniAI Engine is running"}
