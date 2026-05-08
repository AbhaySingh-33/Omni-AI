import re
from typing import Dict, List, Optional

from legal_rag.neo4j_store import LegalGraphStore


MAX_CANDIDATES = 8
MAX_CONTEXT_NODES = 28

INTENT_NODETYPE_MAP = {
    "issue": ["section", "article", "rule", "paragraph"],
    "facts": ["paragraph", "section", "clause"],
    "statute": ["section", "article", "rule", "clause"],
    "procedure": ["paragraph", "section", "order"],
    "reasoning": ["paragraph", "analysis", "judgment"],
    "holding": ["judgment", "order", "paragraph"],
    "timeline": ["paragraph", "section"],
    "relief": ["order", "judgment", "paragraph"],
    "summary": ["paragraph", "section", "judgment"],
}


class LegalGraphRetriever:
    def __init__(self, store: Optional[LegalGraphStore] = None) -> None:
        self.store = store or LegalGraphStore()

    def find_candidate_nodes(
        self,
        user_id: str,
        question: str,
        doc_id: Optional[str] = None,
        query_variants: Optional[List[str]] = None,
        preferred_sections: Optional[List[str]] = None,
        preferred_node_types: Optional[List[str]] = None,
        citations: Optional[List[str]] = None,
    ) -> List[Dict]:
        terms = _query_terms([question] + (query_variants or []))
        sections = [s.lower() for s in (preferred_sections or [])]
        node_types = [n.lower() for n in (preferred_node_types or [])]
        quoted_citations = [c.lower().strip() for c in (citations or []) if str(c).strip()]
        with self.store.driver.session() as session:
            result = session.run(
                """
                MATCH (n:LegalNode {user_id: $user_id})
                WHERE ($doc_id IS NULL OR n.doc_id = $doc_id)
                  AND n.node_type <> 'document'
                  AND (
                    any(term IN $terms WHERE toLower(n.title) CONTAINS term)
                    OR any(term IN $terms WHERE toLower(coalesce(n.search_text, n.text)) CONTAINS term)
                    OR any(term IN $terms WHERE toLower(coalesce(n.identifier, '')) = term)
                    OR any(cit IN $citations WHERE any(node_cit IN coalesce(n.citations, []) WHERE toLower(node_cit) CONTAINS cit))
                  )
                 WITH n,
                     size([term IN $terms WHERE toLower(coalesce(n.search_text, n.text, '')) CONTAINS term]) AS lexical_hits,
                     CASE WHEN size($sections) = 0 THEN 0
                         WHEN any(sec IN $sections WHERE toLower(coalesce(n.section_path, '')) CONTAINS sec OR toLower(coalesce(n.section_tag, '')) = sec) THEN 2
                         ELSE 0 END AS section_boost,
                     CASE WHEN size($node_types) = 0 THEN 0
                         WHEN toLower(coalesce(n.node_type, 'paragraph')) IN $node_types THEN 2
                         ELSE 0 END AS nodetype_boost,
                     CASE WHEN size($citations) = 0 THEN 0
                         WHEN any(cit IN $citations WHERE any(node_cit IN coalesce(n.citations, []) WHERE toLower(node_cit) CONTAINS cit)) THEN 3
                         ELSE 0 END AS citation_boost,
                     size([(n)-[:REFERENCES]->() | 1]) AS ref_count,
                     size([(n)-[:HAS_EVENT]->() | 1]) AS event_count
                 WITH n, lexical_hits, section_boost, nodetype_boost, citation_boost, ref_count, event_count,
                     (lexical_hits * 1.0) + section_boost + nodetype_boost + citation_boost + (ref_count * 0.1) + (event_count * 0.2) AS retrieval_score
                 RETURN n{.*, retrieval_score: retrieval_score} AS node
                 ORDER BY retrieval_score DESC, n.depth ASC, n.order_index ASC
                LIMIT $limit
                """,
                user_id=user_id,
                doc_id=doc_id,
                terms=terms,
                sections=sections,
                node_types=node_types,
                citations=quoted_citations,
                limit=MAX_CANDIDATES,
            )
            return [dict(row["node"]) for row in result]

    def expand_context(self, user_id: str, candidate_node_ids: List[str]) -> Dict:
        if not candidate_node_ids:
            return {"nodes": [], "references": [], "acts": []}

        with self.store.driver.session() as session:
            rows = session.run(
                """
                UNWIND $candidate_ids AS nid
                MATCH (seed:LegalNode {user_id: $user_id, node_id: nid})
                OPTIONAL MATCH path_up = (ancestor:LegalNode {user_id: $user_id})-[:HAS_CHILD*1..4]->(seed)
                OPTIONAL MATCH path_down = (seed)-[:HAS_CHILD*1..2]->(descendant:LegalNode {user_id: $user_id})
                WITH collect(DISTINCT seed) + collect(DISTINCT ancestor) + collect(DISTINCT descendant) AS all_nodes
                UNWIND all_nodes AS n
                WITH DISTINCT n
                OPTIONAL MATCH (n)-[r:REFERENCES]->(target)
                  OPTIONAL MATCH (n)-[:HAS_EVENT]->(ev:LegalEvent)-[:INVOLVES]->(party:LegalParty)
                RETURN n{.*} AS node,
                      collect(DISTINCT {ref_type: r.ref_type, target_label: r.target_label, target_kind: head(labels(target)), target: target{.*}}) AS refs,
                        collect(DISTINCT {subject: ev.subject, action: ev.action, object: ev.object, party: party.name, source_page: n.page_start}) AS events
                LIMIT $limit
                """,
                user_id=user_id,
                candidate_ids=candidate_node_ids,
                limit=MAX_CONTEXT_NODES,
            )

            nodes: List[Dict] = []
            refs: List[Dict] = []
            acts: Dict[str, Dict] = {}
            events: List[Dict] = []
            for row in rows:
                node = row["node"]
                nodes.append(node)
                for ref in row["refs"] or []:
                    if not ref or not ref.get("target_label"):
                        continue
                    refs.append(
                        {
                            "source_node_id": node.get("node_id"),
                            "ref_type": ref.get("ref_type"),
                            "target_label": ref.get("target_label"),
                            "target_kind": ref.get("target_kind"),
                        }
                    )
                    if ref.get("target_kind") == "LegalAct" and isinstance(ref.get("target"), dict):
                        act = ref.get("target")
                        acts[act.get("name", ref.get("target_label"))] = {
                            "name": act.get("name", ref.get("target_label")),
                            "description": act.get("description", ""),
                            "source_url": act.get("source_url", ""),
                        }
                for event in row.get("events") or []:
                    if not event or not event.get("action"):
                        continue
                    events.append(
                        {
                            "source_node_id": node.get("node_id"),
                            "subject": event.get("subject", ""),
                            "action": event.get("action", ""),
                            "object": event.get("object", ""),
                            "party": event.get("party", ""),
                        }
                    )

        nodes_sorted = sorted(nodes, key=lambda n: (n.get("page_start", 0), n.get("depth", 0), n.get("order_index", 0)))
        refs_dedup = list({(r["source_node_id"], r["ref_type"], r["target_label"]): r for r in refs}.values())
        events_dedup = list({(e["source_node_id"], e["subject"], e["action"], e["object"]): e for e in events}.values())
        return {"nodes": nodes_sorted, "references": refs_dedup, "acts": list(acts.values()), "events": events_dedup}

    def format_context(self, expanded: Dict) -> str:
        lines: List[str] = []

        for node in expanded.get("nodes", []):
            node_type = node.get("node_type", "node")
            title = node.get("title", "")
            page = node.get("page_start", "")
            text = (node.get("text") or "").strip()
            excerpt = text[:450] + ("..." if len(text) > 450 else "")
            lines.append(f"[{node_type}] p.{page} {title}")
            if excerpt:
                lines.append(f"  {excerpt}")

        if expanded.get("references"):
            lines.append("\nReferences:")
            for ref in expanded["references"][:40]:
                lines.append(
                    f"- {ref.get('source_node_id')} -> ({ref.get('ref_type')}) {ref.get('target_label')}"
                )

        if expanded.get("acts"):
            lines.append("\nActs:")
            for act in expanded["acts"][:20]:
                desc = (act.get("description") or "").strip()
                if desc:
                    lines.append(f"- {act.get('name')}: {desc[:250]}")
                else:
                    lines.append(f"- {act.get('name')}: [missing description]")

        if expanded.get("events"):
            lines.append("\nEvents:")
            for event in expanded["events"][:40]:
                lines.append(
                    f"- p.{event.get('source_page', '?')} {event.get('subject')} {event.get('action')} {event.get('object')}"
                )

        return "\n".join(lines)


def _query_terms(texts: List[str]) -> List[str]:
    corpus = " ".join([t for t in texts if t])
    tokens = [t.lower() for t in re.findall(r"[A-Za-z0-9\.\-]{3,}", corpus)]
    dedup: List[str] = []
    for token in tokens:
        if token not in dedup:
            dedup.append(token)
    return dedup[:18]


def intent_default_node_types(intent: str) -> List[str]:
    return INTENT_NODETYPE_MAP.get(intent.lower().strip(), INTENT_NODETYPE_MAP["summary"])
