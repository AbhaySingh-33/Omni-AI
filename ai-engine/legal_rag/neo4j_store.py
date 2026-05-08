import hashlib
import json
import re
from typing import Dict, List, Optional, Tuple

from app.gemini import llm
from database.neo4j_loader import Neo4jLoader
from legal_rag.models import LegalDocumentMeta, LegalNode, LegalReference
from legal_rag.prompts import EVENT_EXTRACTION_PROMPT
from legal_rag.schema import LEGAL_KG_SCHEMA


class LegalGraphStore:
    def __init__(self) -> None:
        self._loader = Neo4jLoader()
        self.driver = self._loader.driver
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        _ = LEGAL_KG_SCHEMA
        with self.driver.session() as session:
            session.run(
                """
                CREATE CONSTRAINT IF NOT EXISTS
                FOR (d:LegalDocument)
                REQUIRE (d.user_id, d.doc_id) IS UNIQUE
                """
            )
            session.run(
                """
                CREATE CONSTRAINT IF NOT EXISTS
                FOR (n:LegalNode)
                REQUIRE (n.user_id, n.node_id) IS UNIQUE
                """
            )
            session.run(
                """
                CREATE CONSTRAINT IF NOT EXISTS
                FOR (a:LegalAct)
                REQUIRE (a.user_id, a.name) IS UNIQUE
                """
            )
            session.run(
                """
                CREATE INDEX IF NOT EXISTS
                FOR (n:LegalNode)
                ON (n.user_id, n.doc_id, n.node_type, n.identifier, n.section_tag, n.section_path)
                """
            )
            session.run(
                """
                CREATE INDEX IF NOT EXISTS
                FOR (n:LegalNode)
                ON (n.user_id, n.doc_id, n.page_start, n.order_index)
                """
            )
            session.run(
                """
                CREATE CONSTRAINT IF NOT EXISTS
                FOR (e:LegalEvent)
                REQUIRE (e.user_id, e.event_id) IS UNIQUE
                """
            )
            session.run(
                """
                CREATE CONSTRAINT IF NOT EXISTS
                FOR (p:LegalParty)
                REQUIRE (p.user_id, p.name) IS UNIQUE
                """
            )

    def upsert_document_tree(
        self,
        meta: LegalDocumentMeta,
        nodes: List[LegalNode],
        references: List[LegalReference],
    ) -> None:
        with self.driver.session() as session:
            session.run(
                """
                MERGE (d:LegalDocument {user_id: $user_id, doc_id: $doc_id})
                ON CREATE SET d.created_at = timestamp()
                SET d.filename = $filename,
                    d.page_count = $page_count,
                    d.updated_at = timestamp()
                """,
                user_id=meta.user_id,
                doc_id=meta.doc_id,
                filename=meta.filename,
                page_count=meta.page_count,
            )

            session.run(
                """
                UNWIND $nodes AS n
                MERGE (node:LegalNode {user_id: n.user_id, node_id: n.node_id})
                ON CREATE SET node.created_at = timestamp()
                SET node.doc_id = n.doc_id,
                    node.node_type = n.node_type,
                    node.title = n.title,
                    node.text = n.text,
                    node.search_text = coalesce(n.search_text, ''),
                    node.section_tag = coalesce(n.section_tag, 'general'),
                    node.section_path = coalesce(n.section_path, ''),
                    node.citations = coalesce(n.citations, []),
                    node.page_start = n.page_start,
                    node.page_end = n.page_end,
                    node.depth = n.depth,
                    node.order_index = n.order_index,
                    node.path = n.path,
                    node.parent_id = n.parent_id,
                    node.identifier = n.identifier,
                    node.updated_at = timestamp()
                """,
                nodes=[n.__dict__ for n in nodes],
            )

            session.run(
                """
                MATCH (d:LegalDocument {user_id: $user_id, doc_id: $doc_id})
                MATCH (root:LegalNode {user_id: $user_id, doc_id: $doc_id, node_type: 'document'})
                MERGE (d)-[:HAS_ROOT]->(root)
                """,
                user_id=meta.user_id,
                doc_id=meta.doc_id,
            )

            session.run(
                """
                UNWIND $nodes AS n
                WITH n WHERE n.parent_id IS NOT NULL
                MATCH (p:LegalNode {user_id: n.user_id, node_id: n.parent_id})
                MATCH (c:LegalNode {user_id: n.user_id, node_id: n.node_id})
                MERGE (p)-[:HAS_CHILD]->(c)
                """,
                nodes=[n.__dict__ for n in nodes],
            )

            # Clean previous references for this document before rebuilding.
            session.run(
                """
                MATCH (:LegalNode {user_id: $user_id, doc_id: $doc_id})-[r:REFERENCES]->()
                DELETE r
                """,
                user_id=meta.user_id,
                doc_id=meta.doc_id,
            )

            for ref in references:
                if ref.target_node_id:
                    session.run(
                        """
                        MATCH (s:LegalNode {user_id: $user_id, node_id: $source_node_id})
                        MATCH (t:LegalNode {user_id: $user_id, node_id: $target_node_id})
                        MERGE (s)-[r:REFERENCES {ref_type: $ref_type, target_label: $target_label}]->(t)
                        ON CREATE SET r.created_at = timestamp()
                        SET r.updated_at = timestamp()
                        """,
                        user_id=ref.user_id,
                        source_node_id=ref.source_node_id,
                        target_node_id=ref.target_node_id,
                        ref_type=ref.ref_type,
                        target_label=ref.target_label,
                    )
                else:
                    session.run(
                        """
                        MERGE (a:LegalAct {user_id: $user_id, name: $target_label})
                        ON CREATE SET a.description = '', a.created_at = timestamp()
                        SET a.updated_at = timestamp()
                        WITH a
                        MATCH (s:LegalNode {user_id: $user_id, node_id: $source_node_id})
                        MERGE (s)-[r:REFERENCES {ref_type: $ref_type, target_label: $target_label}]->(a)
                        ON CREATE SET r.created_at = timestamp()
                        SET r.updated_at = timestamp()
                        """,
                        user_id=ref.user_id,
                        source_node_id=ref.source_node_id,
                        ref_type=ref.ref_type,
                        target_label=ref.target_label,
                    )

            self._upsert_events(meta.user_id, meta.doc_id, nodes)

    def list_documents(self, user_id: str) -> List[Dict]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (d:LegalDocument {user_id: $user_id})
                OPTIONAL MATCH (d)-[:HAS_ROOT]->(root:LegalNode)
                OPTIONAL MATCH (root)-[:HAS_CHILD*0..]->(n:LegalNode)
                RETURN d.doc_id AS doc_id,
                       d.filename AS filename,
                       d{.*} AS doc_props,
                       count(DISTINCT n) AS nodes,
                       d.updated_at AS updated_at
                ORDER BY d.updated_at DESC
                """,
                user_id=user_id,
            )
            rows: List[Dict] = []
            for row in result:
                data = dict(row)
                props = data.pop("doc_props", {}) or {}
                data["page_count"] = int(props.get("page_count") or 0)
                rows.append(data)
            return rows

    def _extract_event_tuples(self, text: str) -> List[Tuple[str, str, str]]:
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        if not cleaned:
            return []

        try:
            prompt = f"""
{EVENT_EXTRACTION_PROMPT}

Text:
{cleaned[:1800]}
"""
            result = llm.invoke(prompt)
            payload = json.loads((getattr(result, "content", "") or "{}").strip())
            events = []
            for item in payload.get("events", [])[:6]:
                subject = str(item.get("subject", "")).strip()
                action = str(item.get("action", "")).strip().lower()
                obj = str(item.get("object", "")).strip()[:220]
                if subject and action and obj:
                    events.append((subject, action, obj))
            if events:
                return events
        except Exception:
            pass

        patterns = [
            re.compile(
                r"\b([A-Z][A-Za-z0-9_\-]{2,}(?:\s+[A-Z][A-Za-z0-9_\-]{2,}){0,3})\b\s+"
                r"(filed|alleged|submitted|observed|held|decided|committed|caused|ordered|argued|directed)\s+(.+?)(?:\.|;|$)",
                re.IGNORECASE,
            )
        ]

        events: List[Tuple[str, str, str]] = []
        for pattern in patterns:
            for match in pattern.finditer(cleaned):
                subject = (match.group(1) or "").strip().title()
                action = (match.group(2) or "").strip().lower()
                obj = (match.group(3) or "").strip()[:220]
                if subject and action and obj:
                    events.append((subject, action, obj))

        return events[:12]

    def _upsert_events(self, user_id: str, doc_id: str, nodes: List[LegalNode]) -> None:
        with self.driver.session() as session:
            session.run(
                """
                MATCH (e:LegalEvent {user_id: $user_id, doc_id: $doc_id})
                DETACH DELETE e
                """,
                user_id=user_id,
                doc_id=doc_id,
            )

            for node in nodes:
                if node.node_type == "document":
                    continue
                if len((node.text or "").strip()) < 30:
                    continue

                events = self._extract_event_tuples(f"{node.title}. {node.text}")
                for subject, action, obj in events:
                    event_id = hashlib.md5(
                        f"{user_id}:{doc_id}:{node.node_id}:{subject}:{action}:{obj}".encode("utf-8")
                    ).hexdigest()
                    session.run(
                        """
                        MATCH (n:LegalNode {user_id: $user_id, node_id: $node_id})
                        MERGE (p:LegalParty {user_id: $user_id, name: $subject})
                        ON CREATE SET p.created_at = timestamp()
                        SET p.updated_at = timestamp()
                        MERGE (e:LegalEvent {user_id: $user_id, event_id: $event_id})
                        ON CREATE SET e.created_at = timestamp()
                        SET e.doc_id = $doc_id,
                            e.source_node_id = $node_id,
                            e.subject = $subject,
                            e.action = $action,
                            e.object = $object,
                            e.event_time = '',
                            e.confidence = 0.7,
                            e.updated_at = timestamp()
                        MERGE (n)-[:HAS_EVENT]->(e)
                        MERGE (e)-[:INVOLVES]->(p)
                        """,
                        user_id=user_id,
                        doc_id=doc_id,
                        node_id=node.node_id,
                        subject=subject,
                        action=action,
                        object=obj,
                        event_id=event_id,
                    )

    def get_node(self, user_id: str, node_id: str) -> Optional[Dict]:
        with self.driver.session() as session:
            row = session.run(
                """
                MATCH (n:LegalNode {user_id: $user_id, node_id: $node_id})
                RETURN n{.*} AS node
                """,
                user_id=user_id,
                node_id=node_id,
            ).single()
            return row["node"] if row else None

    def count_content_nodes(self, user_id: str, doc_id: str) -> int:
        with self.driver.session() as session:
            row = session.run(
                """
                MATCH (n:LegalNode {user_id: $user_id, doc_id: $doc_id})
                WHERE n.node_type <> 'document'
                  AND size(coalesce(n.text, '')) > 0
                RETURN count(n) AS cnt
                """,
                user_id=user_id,
                doc_id=doc_id,
            ).single()
            return int(row["cnt"] if row else 0)

    def update_act_description(self, user_id: str, act_name: str, description: str, source_url: str = "") -> None:
        with self.driver.session() as session:
            session.run(
                """
                MERGE (a:LegalAct {user_id: $user_id, name: $name})
                ON CREATE SET a.created_at = timestamp()
                SET a.description = $description,
                    a.source_url = $source_url,
                    a.updated_at = timestamp()
                """,
                user_id=user_id,
                name=act_name,
                description=description,
                source_url=source_url,
            )

    def delete_document(self, user_id: str, doc_id: str) -> int:
        with self.driver.session() as session:
            count_row = session.run(
                """
                MATCH (n:LegalNode {user_id: $user_id, doc_id: $doc_id})
                RETURN count(n) AS cnt
                """,
                user_id=user_id,
                doc_id=doc_id,
            ).single()
            count = int(count_row["cnt"]) if count_row else 0

            session.run(
                """
                MATCH (n:LegalNode {user_id: $user_id, doc_id: $doc_id})
                DETACH DELETE n
                """,
                user_id=user_id,
                doc_id=doc_id,
            )
            session.run(
                """
                MATCH (e:LegalEvent {user_id: $user_id, doc_id: $doc_id})
                DETACH DELETE e
                """,
                user_id=user_id,
                doc_id=doc_id,
            )
            session.run(
                """
                MATCH (d:LegalDocument {user_id: $user_id, doc_id: $doc_id})
                DETACH DELETE d
                """,
                user_id=user_id,
                doc_id=doc_id,
            )
            session.run(
                """
                MATCH (a:LegalAct {user_id: $user_id})
                WHERE a.description = '' AND NOT ()-[:REFERENCES]->(a)
                DELETE a
                """,
                user_id=user_id,
            )
            session.run(
                """
                MATCH (p:LegalParty {user_id: $user_id})
                WHERE NOT ()-[:INVOLVES]->(p)
                DELETE p
                """,
                user_id=user_id,
            )
            return count
