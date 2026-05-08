import os
import shutil
import tempfile
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from neo4j.exceptions import ServiceUnavailable
from pydantic import BaseModel

from app.auth import get_current_user
from legal_rag.service import LegalVectorlessRAGService


router = APIRouter(prefix="/legal-rag", tags=["legal-rag"])


@lru_cache(maxsize=1)
def _service() -> LegalVectorlessRAGService:
    return LegalVectorlessRAGService()


class LegalQueryRequest(BaseModel):
    question: str
    doc_id: Optional[str] = None


@router.get("/health")
def legal_rag_health(user=Depends(get_current_user)):
    uri = os.getenv("NEO4J_URI") or ""
    return {
        "ok": True,
        "neo4j_uri_set": bool(uri),
        "neo4j_uri_preview": uri[:18] + "..." if uri else None,
        "user_id": user.get("user_id"),
    }


@router.get("/schema")
def legal_rag_schema(user=Depends(get_current_user)):
    try:
        schema = _service().schema()
    except ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not load legal schema: {exc}")
    return {"status": "ok", "schema": schema}


@router.post("/upload")
async def upload_legal_pdf(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = await run_in_threadpool(_service().ingest_pdf, tmp_path, file.filename, user["user_id"])
    except ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Legal ingest failed: {exc}")
    finally:
        os.unlink(tmp_path)

    return {"status": "ok", **result}


@router.post("/query")
async def query_legal_rag(req: LegalQueryRequest, user=Depends(get_current_user)):
    question = (req.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    try:
        result = await run_in_threadpool(_service().query, question, user["user_id"], req.doc_id)
    except ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Legal query failed: {exc}")

    return {"status": "ok", **result}


@router.get("/documents")
def list_legal_documents(user=Depends(get_current_user)):
    try:
        docs = _service().list_documents(user["user_id"])
    except ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not list legal docs: {exc}")
    return {"documents": docs}


@router.delete("/documents/{doc_id}")
def delete_legal_document(doc_id: str, user=Depends(get_current_user)):
    try:
        deleted = _service().delete_document(user["user_id"], doc_id)
    except ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not delete legal doc: {exc}")

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"status": "ok", "deleted_nodes": deleted}
