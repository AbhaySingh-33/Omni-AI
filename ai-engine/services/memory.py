from app.db import cursor, conn

def save_chat(user_id, message, response):
    cursor.execute(
        "INSERT INTO chat_history (user_id, message, response) VALUES (%s, %s, %s)",
        (user_id, message, response)
    )
    conn.commit()


def get_history(user_id, limit=5):
    cursor.execute(
        "SELECT message, response FROM chat_history WHERE user_id=%s ORDER BY created_at DESC LIMIT %s",
        (user_id, limit)
    )
    return cursor.fetchall()