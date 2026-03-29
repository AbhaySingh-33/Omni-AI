from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import os

from app.auth import get_current_user
from services.kg import query_kg, list_entities, list_relations, list_entities_for_document

router = APIRouter()


@router.get("/kg/health")
def kg_health(user=Depends(get_current_user)):
    uri = os.getenv("NEO4J_URI") or ""
    user_env = os.getenv("NEO4J_USER") or ""
    pwd = os.getenv("NEO4J_PASSWORD") or ""

    return {
        "neo4j_uri_set": bool(uri),
        "neo4j_user_set": bool(user_env),
        "neo4j_password_set": bool(pwd),
        "neo4j_uri_preview": uri[:18] + "..." if uri else None,
    }


@router.get("/kg/inspect")
def inspect_kg(
    q: Optional[str] = None,
    limit: int = 20,
    doc_id: Optional[str] = None,
    source_type: Optional[str] = None,
    user=Depends(get_current_user),
):
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")

    user_id = user["user_id"]

    try:
        if q:
            rows = query_kg(q, user_id, limit=limit)
            return {"mode": "search", "query": q, "rows": rows}

        if doc_id:
            entities = list_entities_for_document(user_id, doc_id, limit=limit)
            relations = list_relations(user_id, limit=limit, source_type=source_type or "document", source_id=doc_id)
            return {
                "mode": "document",
                "doc_id": doc_id,
                "entities": entities,
                "relations": relations,
            }

        entities = list_entities(user_id, limit=limit)
        relations = list_relations(user_id, limit=limit, source_type=source_type)
        return {
            "mode": "overview",
            "entities": entities,
            "relations": relations,
        }
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))