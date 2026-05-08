"""
Clear OmniAI knowledge-graph data from Neo4j.

Usage (from ai-engine/):
  python scripts/clear_neo4j_kg.py --all
  python scripts/clear_neo4j_kg.py --user-id <user_id>

This removes only app KG labels:
    Document, Message, Entity, LegalDocument, LegalNode, LegalAct, LegalEvent, LegalParty
"""

import argparse
import sys
from pathlib import Path

# Ensure local imports work when running as a script.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.neo4j_loader import Neo4jLoader

KG_LABEL_FILTER = "n:Document OR n:Message OR n:Entity OR n:LegalDocument OR n:LegalNode OR n:LegalAct OR n:LegalEvent OR n:LegalParty"


def _count_candidates(session, user_id: str | None) -> int:
    row = session.run(
        f"""
        MATCH (n)
        WHERE ({KG_LABEL_FILTER})
          AND ($user_id IS NULL OR n.user_id = $user_id)
        RETURN count(n) AS cnt
        """,
        user_id=user_id,
    ).single()
    return int(row["cnt"] if row else 0)


def _delete_candidates(session, user_id: str | None) -> int:
    row = session.run(
        f"""
        MATCH (n)
        WHERE ({KG_LABEL_FILTER})
          AND ($user_id IS NULL OR n.user_id = $user_id)
        WITH collect(n) AS nodes
        FOREACH (x IN nodes | DETACH DELETE x)
        RETURN size(nodes) AS deleted
        """,
        user_id=user_id,
    ).single()
    return int(row["deleted"] if row else 0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete OmniAI KG data from Neo4j")
    parser.add_argument("--user-id", type=str, default=None, help="Delete KG only for this user_id")
    parser.add_argument("--all", action="store_true", help="Delete KG for all users")
    args = parser.parse_args()

    if not args.all and not args.user_id:
        print("[ERROR] Provide either --all or --user-id <id>")
        return 2

    scope_user_id = None if args.all else args.user_id

    loader = Neo4jLoader()
    try:
        loader.driver.verify_connectivity()
    except Exception as exc:
        print(f"[ERROR] Neo4j connectivity failed: {exc}")
        loader.close()
        return 1

    with loader.driver.session() as session:
        before = _count_candidates(session, scope_user_id)
        print(f"[INFO] KG nodes matching scope: {before}")
        deleted = _delete_candidates(session, scope_user_id)
        after = _count_candidates(session, scope_user_id)

    loader.close()

    print(f"[DONE] Deleted nodes: {deleted}")
    print(f"[DONE] Remaining nodes in scope: {after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
