import json
import re
import uuid
import concurrent.futures
from typing import Dict, List

from app.gemini import llm
from database.neo4j_loader import Neo4jLoader
from services.text_chunker import chunk_text


import threading

_neo4j_loader = None
_loader_lock = threading.Lock()


def _get_loader():
    global _neo4j_loader
    with _loader_lock:
        if _neo4j_loader is None:
            _neo4j_loader = Neo4jLoader()
    return _neo4j_loader


def _clean_text(content):
    if isinstance(content, list):
        return "".join([item.get("text", "") for item in content if isinstance(item, dict)])
    return content or ""


def _extract_json(text: str):
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def extract_kg(text: str) -> Dict[str, List[Dict[str, str]]]:
    prompt = f"""
Extract a compact knowledge graph from the text.
Return ONLY valid JSON in this format:
{{"entities":[{{"name":"...","type":"..."}}],"relations":[{{"source":"...","relation":"...","target":"..."}}]}}

Rules:
- Use short, canonical entity names.
- Use specific types like Person, Organization, Place, Concept, Product, Event, Document, Date.
- Include only high-confidence facts.
- Keep it concise (max 15 entities, 20 relations).

Text:
{text}
"""

    result = llm.invoke(prompt)
    content = _clean_text(result.content)
    data = _extract_json(content)
    if not data:
        return {"entities": [], "relations": []}

    entities = [
        {"name": e.get("name", "").strip(), "type": e.get("type", "Entity").strip()}
        for e in data.get("entities", [])
        if isinstance(e, dict) and e.get("name")
    ]
    relations = [
        {
            "source": r.get("source", "").strip(),
            "relation": r.get("relation", "").strip(),
            "target": r.get("target", "").strip(),
        }
        for r in data.get("relations", [])
        if isinstance(r, dict) and r.get("source") and r.get("relation") and r.get("target")
    ]

    return {"entities": entities[:15], "relations": relations[:20]}


def _upsert_entities_and_mentions(entities, user_id, source_type, source_id, filename=None, message_text=None):
    if not entities:
        return

    loader = _get_loader()

    with loader.driver.session() as session:
        if source_type == "document":
            session.run(
                """
                MERGE (d:Document {user_id: $user_id, doc_id: $doc_id})
                SET d.filename = $filename, d.updated_at = timestamp()
                """,
                user_id=user_id,
                doc_id=source_id,
                filename=filename,
            )

            session.run(
                """
                UNWIND $entities AS ent
                MERGE (e:Entity {user_id: $user_id, name: ent.name, type: ent.type})
                ON CREATE SET e.created_at = timestamp()
                SET e.updated_at = timestamp()
                WITH e
                MATCH (d:Document {user_id: $user_id, doc_id: $doc_id})
                MERGE (d)-[:MENTIONS {user_id: $user_id, source_id: $doc_id, source_type: 'document'}]->(e)
                """,
                user_id=user_id,
                doc_id=source_id,
                entities=entities,
            )

        if source_type == "message":
            session.run(
                """
                MERGE (m:Message {user_id: $user_id, message_id: $message_id})
                SET m.text = $text, m.updated_at = timestamp()
                """,
                user_id=user_id,
                message_id=source_id,
                text=message_text,
            )

            session.run(
                """
                UNWIND $entities AS ent
                MERGE (e:Entity {user_id: $user_id, name: ent.name, type: ent.type})
                ON CREATE SET e.created_at = timestamp()
                SET e.updated_at = timestamp()
                WITH e
                MATCH (m:Message {user_id: $user_id, message_id: $message_id})
                MERGE (m)-[:MENTIONS {user_id: $user_id, source_id: $message_id, source_type: 'message'}]->(e)
                """,
                user_id=user_id,
                message_id=source_id,
                entities=entities,
            )


def _upsert_relations(relations, entities, user_id, source_type, source_id):
    if not relations:
        return

    entity_type_map = {e["name"].lower(): e.get("type", "Entity") for e in entities}
    enriched = []
    for rel in relations:
        source = rel["source"].strip()
        target = rel["target"].strip()
        if not source or not target:
            continue
        enriched.append({
            "source": source,
            "target": target,
            "relation": rel["relation"].strip(),
            "source_type": entity_type_map.get(source.lower(), "Entity"),
            "target_type": entity_type_map.get(target.lower(), "Entity"),
        })

    if not enriched:
        return

    loader = _get_loader()
    with loader.driver.session() as session:
        session.run(
            """
            UNWIND $relations AS rel
            MERGE (s:Entity {user_id: $user_id, name: rel.source, type: rel.source_type})
            ON CREATE SET s.created_at = timestamp()
            SET s.updated_at = timestamp()
            MERGE (t:Entity {user_id: $user_id, name: rel.target, type: rel.target_type})
            ON CREATE SET t.created_at = timestamp()
            SET t.updated_at = timestamp()
            MERGE (s)-[r:REL {user_id: $user_id, source_id: $source_id, source_type: $source_type, type: rel.relation}]->(t)
            ON CREATE SET r.created_at = timestamp()
            SET r.updated_at = timestamp()
            """,
            user_id=user_id,
            source_id=source_id,
            source_type=source_type,
            relations=enriched,
        )


def ingest_document_text(text: str, doc_id: str, filename: str, user_id: str):
    chunks = chunk_text(text)
    
    def process_chunk(chunk):
        try:
            kg = extract_kg(chunk)
            entities = kg.get("entities", [])
            relations = kg.get("relations", [])
            if not entities and not relations:
                return
            _upsert_entities_and_mentions(entities, user_id, "document", doc_id, filename=filename)
            _upsert_relations(relations, entities, user_id, "document", doc_id)
        except Exception as e:
            print(f"Error processing chunk for KG: {e}")

    # Process chunks in parallel using ThreadPoolExecutor
    print(f"Ingesting {len(chunks)} chunks into KG for doc: {doc_id} with parallel threads...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(process_chunk, chunks))


def ingest_user_message(message: str, user_id: str):
    kg = extract_kg(message)
    entities = kg.get("entities", [])
    relations = kg.get("relations", [])
    if not entities and not relations:
        return None

    message_id = uuid.uuid4().hex
    _upsert_entities_and_mentions(entities, user_id, "message", message_id, message_text=message)
    _upsert_relations(relations, entities, user_id, "message", message_id)
    return message_id


def query_kg(query: str, user_id: str, limit: int = 10):
    loader = _get_loader()
    with loader.driver.session() as session:
        result = session.run(
            """
            MATCH (e:Entity {user_id: $user_id})
            WHERE toLower(e.name) CONTAINS toLower($search_query)
            OPTIONAL MATCH (e)-[r:REL {user_id: $user_id}]->(t:Entity {user_id: $user_id})
            RETURN e.name as entity, e.type as type,
                   collect({relation: r.type, target: t.name}) as relationships
            LIMIT $limit
            """,
            search_query=query,
            user_id=user_id,
            limit=limit,
        )
        return [dict(record) for record in result]


def delete_kg_for_document(doc_id: str, user_id: str):
    loader = _get_loader()
    with loader.driver.session() as session:
        session.run(
            """
            MATCH ()-[r:REL {user_id: $user_id, source_type: 'document', source_id: $doc_id}]->()
            DELETE r
            """,
            user_id=user_id,
            doc_id=doc_id,
        )
        session.run(
            """
            MATCH (d:Document {user_id: $user_id, doc_id: $doc_id})
            OPTIONAL MATCH (d)-[m:MENTIONS]->()
            DELETE m
            DETACH DELETE d
            """,
            user_id=user_id,
            doc_id=doc_id,
        )
        session.run(
            """
            MATCH (e:Entity {user_id: $user_id})
            WHERE NOT (e)--()
            DELETE e
            """,
            user_id=user_id,
        )


def format_kg_context(rows):
    lines = []
    for r in rows:
        rels = ", ".join([
            f"{rel['relation']} {rel['target']}" for rel in r.get("relationships", []) if rel.get("target")
        ])
        if rels:
            lines.append(f"- {r['entity']} ({r['type']}): {rels}")
    return "\n".join(lines)

def list_entities(user_id: str, limit: int = 20):
    loader = _get_loader()
    with loader.driver.session() as session:
        result = session.run(
            """
            MATCH (e:Entity {user_id: $user_id})
            RETURN e.name AS name, e.type AS type, e.updated_at AS updated_at
            ORDER BY e.updated_at DESC
            LIMIT $limit
            """,
            user_id=user_id,
            limit=limit,
        )
        return [dict(record) for record in result]


def list_relations(user_id: str, limit: int = 20, source_type: str = None, source_id: str = None):
    loader = _get_loader()
    with loader.driver.session() as session:
        result = session.run(
            """
            MATCH (s:Entity {user_id: $user_id})-[r:REL {user_id: $user_id}]->(t:Entity {user_id: $user_id})
            WHERE ($source_type IS NULL OR r.source_type = $source_type)
              AND ($source_id IS NULL OR r.source_id = $source_id)
            RETURN s.name AS source, r.type AS relation, t.name AS target,
                   r.source_type AS source_type, r.source_id AS source_id,
                   r.updated_at AS updated_at
            ORDER BY r.updated_at DESC
            LIMIT $limit
            """,
            user_id=user_id,
            source_type=source_type,
            source_id=source_id,
            limit=limit,
        )
        return [dict(record) for record in result]


def list_entities_for_document(user_id: str, doc_id: str, limit: int = 50):
    loader = _get_loader()
    with loader.driver.session() as session:
        result = session.run(
            """
            MATCH (d:Document {user_id: $user_id, doc_id: $doc_id})-[:MENTIONS]->(e:Entity {user_id: $user_id})
            RETURN DISTINCT e.name AS name, e.type AS type, e.updated_at AS updated_at
            ORDER BY e.updated_at DESC
            LIMIT $limit
            """,
            user_id=user_id,
            doc_id=doc_id,
            limit=limit,
        )
        return [dict(record) for record in result]
