from app.db import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    message TEXT,
    response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS summarized_memory (
    id SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    summary TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS emotion_log (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    emotion TEXT NOT NULL,
    confidence FLOAT,
    intensity TEXT,
    risk_level TEXT,
    scores TEXT,
    is_crisis BOOLEAN DEFAULT FALSE,
    message_snippet TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE INDEX IF NOT EXISTS idx_emotion_log_user_date
    ON emotion_log(user_id, created_at DESC)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS emotion_alerts (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    risk_level TEXT,
    details TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
cur.close()
print("Tables created successfully (including emotion tables).")
