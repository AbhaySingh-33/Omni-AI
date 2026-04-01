"""
Emotion Store — Database operations for emotion tracking.
==========================================================
Persists emotion results, risk assessments, and alerts to PostgreSQL.
Provides query functions for trend analysis and analytics dashboard.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from app.db import get_connection


# ---------------------------------------------------------------------------
# Table initialization (called on startup)
# ---------------------------------------------------------------------------

def init_emotion_tables():
    """Create emotion tables if they don't exist."""
    conn = get_connection()
    with conn.cursor() as cur:
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


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

def save_emotion(
    user_id: str,
    emotion: str,
    confidence: float,
    intensity: str,
    risk_level: str,
    scores: Dict[str, float],
    is_crisis: bool,
    message_snippet: str = "",
):
    """Persist a single emotion detection result."""
    conn = get_connection()
    snippet = (message_snippet[:100] + "...") if len(message_snippet) > 100 else message_snippet
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO emotion_log
                (user_id, emotion, confidence, intensity, risk_level, scores, is_crisis, message_snippet)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, emotion, confidence, intensity, risk_level,
             json.dumps(scores), is_crisis, snippet),
        )
    conn.commit()


def save_alert(user_id: str, alert_type: str, risk_level: str, details: str):
    """Save an alert (risk escalation, crisis, trend worsening)."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO emotion_alerts (user_id, alert_type, risk_level, details)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, alert_type, risk_level, details),
        )
    conn.commit()


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def get_recent_emotions(user_id: str, limit: int = 7) -> List[Dict[str, Any]]:
    """
    Fetch the N most recent emotion entries for a user.
    Returns list of dicts sorted oldest → newest.
    """
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT emotion, confidence, intensity, risk_level, scores,
                   is_crisis, created_at
            FROM emotion_log
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        rows = cur.fetchall()

    results = []
    for row in reversed(rows):  # oldest first
        scores_raw = row[4]
        try:
            scores = json.loads(scores_raw) if isinstance(scores_raw, str) else scores_raw
        except (json.JSONDecodeError, TypeError):
            scores = {}
        results.append({
            "emotion": row[0],
            "confidence": row[1],
            "intensity": row[2],
            "risk_level": row[3],
            "scores": scores,
            "is_crisis": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
        })
    return results


def get_emotion_history(user_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """
    Fetch emotion history for last N days.
    Groups by day with the dominant emotion per day.
    """
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                DATE(created_at) as day,
                emotion,
                AVG(confidence) as avg_confidence,
                MAX(CASE WHEN is_crisis THEN 1 ELSE 0 END) as had_crisis,
                COUNT(*) as msg_count
            FROM emotion_log
            WHERE user_id = %s
              AND created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(created_at), emotion
            ORDER BY day ASC, avg_confidence DESC
            """,
            (user_id, days),
        )
        rows = cur.fetchall()

    # Group by day, pick dominant emotion
    daily: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        day_str = row[0].isoformat() if row[0] else ""
        if day_str not in daily:
            daily[day_str] = {
                "date": day_str,
                "emotion": row[1],
                "confidence": round(float(row[2]), 3),
                "had_crisis": bool(row[3]),
                "message_count": row[4],
            }
    return list(daily.values())


def get_emotion_trend(user_id: str, days: int = 7) -> List[Dict[str, Any]]:
    """
    Fetch daily emotion scores for trend visualization.
    Returns one entry per day with average scores across all categories.
    """
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT scores, confidence, emotion, created_at
            FROM emotion_log
            WHERE user_id = %s
              AND created_at >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY created_at ASC
            """,
            (user_id, days),
        )
        rows = cur.fetchall()

    entries = []
    for row in rows:
        scores_raw = row[0]
        try:
            scores = json.loads(scores_raw) if isinstance(scores_raw, str) else scores_raw
        except (json.JSONDecodeError, TypeError):
            scores = {}
        entries.append({
            "scores": scores or {},
            "confidence": float(row[1]) if row[1] else 0.0,
            "emotion": row[2],
            "created_at": row[3].isoformat() if row[3] else None,
        })
    return entries


def get_active_alerts(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch recent unacknowledged alerts."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, alert_type, risk_level, details, created_at
            FROM emotion_alerts
            WHERE user_id = %s AND acknowledged = FALSE
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "alert_type": row[1],
            "risk_level": row[2],
            "details": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
        }
        for row in rows
    ]


def acknowledge_alert(alert_id: int):
    """Mark an alert as acknowledged."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE emotion_alerts SET acknowledged = TRUE WHERE id = %s",
            (alert_id,),
        )
    conn.commit()


def get_user_analytics(user_id: str) -> Dict[str, Any]:
    """
    Full analytics payload for the dashboard.
    Combines current state, trend, and alerts.
    """
    recent = get_recent_emotions(user_id, limit=1)
    current = recent[0] if recent else None

    return {
        "current_emotion": current,
        "history": get_emotion_history(user_id, days=30),
        "trend": get_emotion_trend(user_id, days=7),
        "alerts": get_active_alerts(user_id),
    }
