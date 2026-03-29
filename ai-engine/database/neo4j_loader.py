import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=False)


class Neo4jLoader:
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        if not uri or not user or not password:
            raise ValueError("NEO4J_URI/NEO4J_USER(or NEO4J_USERNAME)/NEO4J_PASSWORD must be set")

        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._ensure_constraints()

    def _ensure_constraints(self):
        with self.driver.session() as session:
            session.run(
                """
                CREATE CONSTRAINT IF NOT EXISTS
                FOR (e:Entity)
                REQUIRE (e.user_id, e.name, e.type) IS UNIQUE
                """
            )
            session.run(
                """
                CREATE CONSTRAINT IF NOT EXISTS
                FOR (d:Document)
                REQUIRE (d.user_id, d.doc_id) IS UNIQUE
                """
            )
            session.run(
                """
                CREATE CONSTRAINT IF NOT EXISTS
                FOR (m:Message)
                REQUIRE (m.user_id, m.message_id) IS UNIQUE
                """
            )
            session.run(
                """
                CREATE INDEX IF NOT EXISTS
                FOR (e:Entity)
                ON (e.user_id, e.name)
                """
            )

    def close(self):
        self.driver.close()