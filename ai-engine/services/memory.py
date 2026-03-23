from app.db import get_connection
from app.gemini import llm

SUMMARIZE_AFTER = 10


def save_chat(user_id, message, response):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chat_history (user_id, message, response) VALUES (%s, %s, %s)",
            (user_id, message, response),
        )
    conn.commit()
    _maybe_summarize(user_id)


def get_history(user_id, limit=20):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT message, response FROM chat_history WHERE user_id=%s ORDER BY created_at ASC LIMIT %s",
            (user_id, limit),
        )
        return cur.fetchall()


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
