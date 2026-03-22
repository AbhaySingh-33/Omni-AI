from app.db import cursor, conn
from app.gemini import llm

SUMMARIZE_AFTER = 10  # compress every N raw messages


def save_chat(user_id, message, response):
    cursor.execute(
        "INSERT INTO chat_history (user_id, message, response) VALUES (%s, %s, %s)",
        (user_id, message, response)
    )
    conn.commit()
    _maybe_summarize(user_id)


def get_history(user_id, limit=5):
    cursor.execute(
        "SELECT message, response FROM chat_history WHERE user_id=%s ORDER BY created_at DESC LIMIT %s",
        (user_id, limit)
    )
    return cursor.fetchall()


def get_summary(user_id):
    cursor.execute(
        "SELECT summary FROM summarized_memory WHERE user_id=%s",
        (user_id,)
    )
    row = cursor.fetchone()
    return row[0] if row else None


def _maybe_summarize(user_id):
    cursor.execute(
        "SELECT COUNT(*) FROM chat_history WHERE user_id=%s",
        (user_id,)
    )
    count = cursor.fetchone()[0]

    if count < SUMMARIZE_AFTER:
        return

    # Fetch all raw chats to summarize
    cursor.execute(
        "SELECT message, response FROM chat_history WHERE user_id=%s ORDER BY created_at ASC",
        (user_id,)
    )
    chats = cursor.fetchall()
    history_text = "\n".join([f"User: {m}\nAI: {r}" for m, r in chats])

    existing_summary = get_summary(user_id)
    prior = f"Prior summary:\n{existing_summary}\n\n" if existing_summary else ""

    prompt = f"""{prior}Summarize the following conversation into a concise memory paragraph capturing key facts, preferences, and context about the user:

{history_text}

Summary:"""

    result = llm.invoke(prompt)
    new_summary = result.content.strip()

    # Upsert summary
    cursor.execute("""
        INSERT INTO summarized_memory (user_id, summary, updated_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (user_id) DO UPDATE SET summary=EXCLUDED.summary, updated_at=NOW()
    """, (user_id, new_summary))

    # Delete compressed raw chats, keep last 5 as recent context
    cursor.execute("""
        DELETE FROM chat_history WHERE user_id=%s AND id NOT IN (
            SELECT id FROM chat_history WHERE user_id=%s ORDER BY created_at DESC LIMIT 5
        )
    """, (user_id, user_id))

    conn.commit()
