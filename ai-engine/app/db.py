import psycopg2
import os
import threading
from dotenv import load_dotenv

load_dotenv()

_local = threading.local()


def _is_connection_alive(conn) -> bool:
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except Exception:
        return False

def get_connection():
    conn = getattr(_local, "conn", None)

    if conn is None or not _is_connection_alive(conn):
        _local.conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")

    return _local.conn
