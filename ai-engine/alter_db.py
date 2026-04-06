import sys
from app.db import get_connection

def alter_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

    try:
        cur.execute("ALTER TABLE chat_history ADD COLUMN session_id TEXT;")
        conn.commit()
        print("Added session_id to chat_history")
    except Exception as e:
        print(f"Error adding session_id (might already exist): {e}")
        conn.rollback()

    cur.close()
    conn.close()

if __name__ == "__main__":
    alter_db()
