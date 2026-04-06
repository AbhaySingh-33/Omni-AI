from app.db import get_connection
from app.gemini import llm

SUMMARIZE_AFTER = 10


def create_session(user_id, session_id, title):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chat_sessions (id, user_id, title) VALUES (%s, %s, %s)",
            (session_id, user_id, title)
        )
    conn.commit()


def get_sessions(user_id):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, created_at FROM chat_sessions WHERE user_id=%s ORDER BY created_at DESC",
            (user_id,)
        )
        return [{"id": row[0], "title": row[1], "createdAt": row[2].isoformat()} for row in cur.fetchall()]


def save_chat(user_id, session_id, message, response):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chat_history (user_id, session_id, message, response) VALUES (%s, %s, %s, %s)",
            (user_id, session_id, message, response),
        )
    conn.commit()
    _maybe_summarize(user_id)


def get_history(user_id, session_id=None, limit=50):
    conn = get_connection()
    with conn.cursor() as cur:
        if session_id:
            cur.execute(
                "SELECT message, response FROM chat_history WHERE user_id=%s AND session_id=%s ORDER BY created_at ASC LIMIT %s",
                (user_id, session_id, limit),
            )
        else:
            cur.execute(
                "SELECT message, response FROM chat_history WHERE user_id=%s AND session_id IS NULL ORDER BY created_at ASC LIMIT %s",
                (user_id, limit),
            )
        return cur.fetchall()


def delete_session(user_id, session_id):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM chat_history WHERE user_id=%s AND session_id=%s", (user_id, session_id))
        cur.execute("DELETE FROM chat_sessions WHERE id=%s AND user_id=%s", (session_id, user_id))
    conn.commit()


def get_summary(user_id):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT summary FROM summarized_memory WHERE user_id=%s",
            (user_id,),
        )
        row = cur.fetchone()
    return row[0] if row else None


def _maybe_summarize(user_id):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM chat_history WHERE user_id=%s", (user_id,)
        )
        count = cur.fetchone()[0]

        if count < SUMMARIZE_AFTER:
            return

        cur.execute(
            "SELECT message, response FROM chat_history WHERE user_id=%s ORDER BY created_at ASC",
            (user_id,),
        )
        chats = cur.fetchall()

    history_text = "\n".join([f"User: {m}\nAI: {r}" for m, r in chats])
    existing_summary = get_summary(user_id)
    prior = f"Prior summary:\n{existing_summary}\n\n" if existing_summary else ""

    prompt = f"""{prior}Summarize the following conversation into a concise memory paragraph:

{history_text}

Summary:"""

    new_summary = llm.invoke(prompt).content.strip()

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO summarized_memory (user_id, summary, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (user_id) DO UPDATE SET summary=EXCLUDED.summary, updated_at=NOW()
            """,
            (user_id, new_summary),
        )
        cur.execute(
            """
            DELETE FROM chat_history WHERE user_id=%s AND id NOT IN (
                SELECT id FROM chat_history WHERE user_id=%s ORDER BY created_at DESC LIMIT 5
            )
            """,
            (user_id, user_id),
        )
    conn.commit()
