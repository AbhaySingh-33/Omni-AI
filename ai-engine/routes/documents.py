from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import tempfile
import os
import shutil

from app.auth import get_current_user
from services.ingest import store_pdf

router = APIRouter()


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        from fastapi.concurrency import run_in_threadpool
        doc_id = await run_in_threadpool(store_pdf, tmp_path, file.filename, user["user_id"])
    finally:
        os.unlink(tmp_path)

    return {"status": "ok", "message": f"'{file.filename}' ingested successfully", "doc_id": doc_id}


@router.get("/documents")
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
            seen[doc_id] = {"doc_id": doc_id, "filename": meta.get("filename", doc_id[:8] + "..."), "chunks": 0}
        if doc_id:
            seen[doc_id]["chunks"] += 1
    return {"documents": list(seen.values()), "total_chunks": stats.get("total_vector_count", 0)}


@router.delete("/documents/{doc_id}")
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

    try:
        from services.kg import delete_kg_for_document
        delete_kg_for_document(doc_id, user["user_id"])
    except Exception as exc:
        print(f"KG delete skipped: {exc}")

    return {"status": "ok", "deleted_chunks": len(ids)}
