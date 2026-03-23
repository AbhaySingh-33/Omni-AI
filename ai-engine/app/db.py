import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

_conn = None

def get_connection():
    global _conn
    try:
        # ping — raises if connection is dead
        if _conn is not None:
            _conn.cursor().execute("SELECT 1")
    except Exception:
        _conn = None

    if _conn is None:
        _conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")

    return _conn
