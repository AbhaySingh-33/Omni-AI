from typing import Dict, Optional

from legal_rag.agentic_workflow import build_legal_agent_graph
from legal_rag.neo4j_store import LegalGraphStore
from legal_rag.parser import parse_legal_pdf
from legal_rag.schema import LEGAL_KG_SCHEMA


class LegalVectorlessRAGService:
    def __init__(self) -> None:
        self.store = LegalGraphStore()
        self.graph = build_legal_agent_graph()

    def ingest_pdf(self, file_path: str, filename: str, user_id: str) -> Dict:
        meta, nodes, references = parse_legal_pdf(file_path=file_path, filename=filename, user_id=user_id)
        content_nodes = [n for n in nodes if n.node_type != "document" and (n.text or "").strip()]
        if not content_nodes:
            raise ValueError(
                "No extractable text found in this PDF. It may be image/scanned-only. "
                "Please run OCR or upload a text-based PDF."
            )
        self.store.upsert_document_tree(meta, nodes, references)
        return {
            "doc_id": meta.doc_id,
            "filename": meta.filename,
            "page_count": meta.page_count,
            "nodes": len(nodes),
            "references": len(references),
        }

    def query(self, question: str, user_id: str, doc_id: Optional[str] = None) -> Dict:
        if doc_id:
            content_count = self.store.count_content_nodes(user_id=user_id, doc_id=doc_id)
            if content_count == 0:
                return {
                    "answer": (
                        "This legal document has no extractable text nodes in the graph. "
                        "It is likely a scanned/image PDF. Please run OCR and re-upload."
                    ),
                    "used_candidates": 0,
                    "context_nodes": 0,
                    "references": 0,
                    "acts": [],
                    "web_enriched": [],
                }

        state = {
            "user_id": user_id,
            "question": question,
            "doc_id": doc_id,
            "intent": "summary",
            "query_terms": [],
            "rewritten_query": "",
            "expanded_queries": [],
            "citations": [],
            "event_focus": [],
            "preferred_node_types": [],
            "preferred_sections": [],
            "candidate_nodes": [],
            "expanded": {"nodes": [], "references": [], "acts": [], "events": []},
            "missing_acts": [],
            "fetched_acts": [],
            "answer": "",
        }
        result = self.graph.invoke(state)
        expanded = result.get("expanded", {})
        return {
            "answer": result.get("answer", ""),
            "intent": result.get("intent", "summary"),
            "preferred_sections": result.get("preferred_sections", []),
            "used_candidates": len(result.get("candidate_nodes", [])),
            "context_nodes": len(expanded.get("nodes", [])),
            "references": len(expanded.get("references", [])),
            "events": len(expanded.get("events", [])),
            "acts": expanded.get("acts", []),
            "web_enriched": result.get("fetched_acts", []),
        }

    def list_documents(self, user_id: str):
        return self.store.list_documents(user_id)

    def delete_document(self, user_id: str, doc_id: str) -> int:
        return self.store.delete_document(user_id, doc_id)

    def schema(self) -> Dict:
        return LEGAL_KG_SCHEMA
