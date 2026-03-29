"""
Interview Prep Database Services

Handles storage and retrieval of:
- User resumes
- Interview sessions
- Mock interview conversations
- Performance feedback and analytics
"""

from app.db import get_connection
from app.gemini import llm
from datetime import datetime
import json


def _parse_json_field(value):
    """Safely parse a JSON field that might be a string, dict, or None."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}


# ============= RESUME SERVICES =============

def save_resume(user_id: str, resume_data: dict) -> int:
    """Save or update user's resume."""
    conn = get_connection()
    with conn.cursor() as cur:
        # Check if user already has a resume
        cur.execute(
            "SELECT id FROM user_resumes WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        existing = cur.fetchone()

        if existing:
            cur.execute(
                """UPDATE user_resumes
                   SET content = %s, parsed_data = %s, updated_at = NOW()
                   WHERE id = %s RETURNING id""",
                (resume_data.get("content", ""), json.dumps(resume_data), existing[0])
            )
        else:
            cur.execute(
                """INSERT INTO user_resumes (user_id, content, parsed_data, created_at, updated_at)
                   VALUES (%s, %s, %s, NOW(), NOW()) RETURNING id""",
                (user_id, resume_data.get("content", ""), json.dumps(resume_data))
            )
        resume_id = cur.fetchone()[0]
    conn.commit()
    return resume_id


def get_resume(user_id: str) -> dict | None:
    """Get user's latest resume."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, content, parsed_data, created_at, updated_at
               FROM user_resumes WHERE user_id = %s
               ORDER BY updated_at DESC LIMIT 1""",
            (user_id,)
        )
        row = cur.fetchone()

    if row:
        return {
            "id": row[0],
            "content": row[1],
            "parsed_data": _parse_json_field(row[2]),
            "created_at": row[3],
            "updated_at": row[4]
        }
    return None


def get_all_resumes(user_id: str) -> list:
    """Get all resumes for a user."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, content, parsed_data, created_at, updated_at
               FROM user_resumes WHERE user_id = %s
               ORDER BY updated_at DESC""",
            (user_id,)
        )
        rows = cur.fetchall()

    return [{
        "id": row[0],
        "content": row[1],
        "parsed_data": _parse_json_field(row[2]),
        "created_at": row[3],
        "updated_at": row[4]
    } for row in rows]


def delete_resume(user_id: str, resume_id: int) -> bool:
    """Delete a specific resume."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM user_resumes WHERE id = %s AND user_id = %s",
            (resume_id, user_id)
        )
        deleted = cur.rowcount > 0
    conn.commit()
    return deleted


# ============= INTERVIEW SESSION SERVICES =============

def create_interview_session(user_id: str, job_title: str, company: str = None,
                            interview_type: str = "general") -> int:
    """Create a new mock interview session."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO interview_sessions
               (user_id, job_title, company, interview_type, status, created_at)
               VALUES (%s, %s, %s, %s, 'in_progress', NOW()) RETURNING id""",
            (user_id, job_title, company, interview_type)
        )
        session_id = cur.fetchone()[0]
    conn.commit()
    return session_id


def save_interview_message(session_id: int, role: str, content: str,
                          question_number: int = None) -> int:
    """Save a message in the interview conversation."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO interview_messages
               (session_id, role, content, question_number, created_at)
               VALUES (%s, %s, %s, %s, NOW()) RETURNING id""",
            (session_id, role, content, question_number)
        )
        message_id = cur.fetchone()[0]
    conn.commit()
    return message_id


def get_interview_session(session_id: int, user_id: str) -> dict | None:
    """Get interview session with all messages."""
    conn = get_connection()
    with conn.cursor() as cur:
        # Get session info
        cur.execute(
            """SELECT id, job_title, company, interview_type, status,
                      created_at, completed_at, overall_score
               FROM interview_sessions WHERE id = %s AND user_id = %s""",
            (session_id, user_id)
        )
        session = cur.fetchone()

        if not session:
            return None

        # Get messages
        cur.execute(
            """SELECT id, role, content, question_number, created_at
               FROM interview_messages WHERE session_id = %s
               ORDER BY created_at ASC""",
            (session_id,)
        )
        messages = cur.fetchall()

    return {
        "id": session[0],
        "job_title": session[1],
        "company": session[2],
        "interview_type": session[3],
        "status": session[4],
        "created_at": session[5],
        "completed_at": session[6],
        "overall_score": session[7],
        "messages": [{
            "id": m[0],
            "role": m[1],
            "content": m[2],
            "question_number": m[3],
            "created_at": m[4]
        } for m in messages]
    }


def get_user_sessions(user_id: str, limit: int = 10) -> list:
    """Get recent interview sessions for a user."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, job_title, company, interview_type, status,
                      created_at, overall_score
               FROM interview_sessions WHERE user_id = %s
               ORDER BY created_at DESC LIMIT %s""",
            (user_id, limit)
        )
        rows = cur.fetchall()

    return [{
        "id": row[0],
        "job_title": row[1],
        "company": row[2],
        "interview_type": row[3],
        "status": row[4],
        "created_at": row[5],
        "overall_score": row[6]
    } for row in rows]


def complete_interview_session(session_id: int, user_id: str, score: float = None):
    """Mark an interview session as completed."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE interview_sessions
               SET status = 'completed', completed_at = NOW(), overall_score = %s
               WHERE id = %s AND user_id = %s""",
            (score, session_id, user_id)
        )
    conn.commit()


# ============= FEEDBACK SERVICES =============

def save_feedback(session_id: int, user_id: str, feedback_data: dict) -> int:
    """Save detailed feedback for an interview session."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO interview_feedback
               (session_id, user_id, overall_score, communication_score,
                content_score, confidence_score, strengths, improvements,
                detailed_feedback, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()) RETURNING id""",
            (
                session_id, user_id,
                feedback_data.get("overall_score"),
                feedback_data.get("communication_score"),
                feedback_data.get("content_score"),
                feedback_data.get("confidence_score"),
                json.dumps(feedback_data.get("strengths", [])),
                json.dumps(feedback_data.get("improvements", [])),
                feedback_data.get("detailed_feedback", "")
            )
        )
        feedback_id = cur.fetchone()[0]
    conn.commit()
    return feedback_id


def get_feedback(session_id: int, user_id: str) -> dict | None:
    """Get feedback for a specific session."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, overall_score, communication_score, content_score,
                      confidence_score, strengths, improvements, detailed_feedback,
                      created_at
               FROM interview_feedback WHERE session_id = %s AND user_id = %s""",
            (session_id, user_id)
        )
        row = cur.fetchone()

    if row:
        return {
            "id": row[0],
            "overall_score": row[1],
            "communication_score": row[2],
            "content_score": row[3],
            "confidence_score": row[4],
            "strengths": _parse_json_field(row[5]) if not isinstance(row[5], list) else row[5],
            "improvements": _parse_json_field(row[6]) if not isinstance(row[6], list) else row[6],
            "detailed_feedback": row[7],
            "created_at": row[8]
        }
    return None


def get_user_progress(user_id: str) -> dict:
    """Get user's interview preparation progress and stats."""
    conn = get_connection()
    with conn.cursor() as cur:
        # Total sessions
        cur.execute(
            "SELECT COUNT(*) FROM interview_sessions WHERE user_id = %s",
            (user_id,)
        )
        total_sessions = cur.fetchone()[0]

        # Completed sessions
        cur.execute(
            "SELECT COUNT(*) FROM interview_sessions WHERE user_id = %s AND status = 'completed'",
            (user_id,)
        )
        completed_sessions = cur.fetchone()[0]

        # Average score
        cur.execute(
            """SELECT AVG(overall_score) FROM interview_feedback
               WHERE user_id = %s AND overall_score IS NOT NULL""",
            (user_id,)
        )
        avg_score = cur.fetchone()[0]

        # Recent scores for trend
        cur.execute(
            """SELECT overall_score, created_at FROM interview_feedback
               WHERE user_id = %s AND overall_score IS NOT NULL
               ORDER BY created_at DESC LIMIT 5""",
            (user_id,)
        )
        recent_scores = cur.fetchall()

        # Has resume
        cur.execute(
            "SELECT COUNT(*) FROM user_resumes WHERE user_id = %s",
            (user_id,)
        )
        has_resume = cur.fetchone()[0] > 0

    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "average_score": float(avg_score) if avg_score else None,
        "recent_scores": [{"score": s[0], "date": s[1]} for s in recent_scores],
        "has_resume": has_resume,
        "improvement_trend": _calculate_trend(recent_scores) if recent_scores else None
    }


def _calculate_trend(scores: list) -> str:
    """Calculate if user is improving, declining, or stable."""
    if len(scores) < 2:
        return "insufficient_data"

    recent = scores[0][0]
    older = scores[-1][0]

    if recent > older + 0.5:
        return "improving"
    elif recent < older - 0.5:
        return "declining"
    return "stable"


# ============= DATABASE INITIALIZATION =============

def init_interview_tables():
    """Create database tables for interview prep features."""
    conn = get_connection()
    with conn.cursor() as cur:
        # User resumes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_resumes (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                content TEXT,
                parsed_data JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Interview sessions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS interview_sessions (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                job_title VARCHAR(255),
                company VARCHAR(255),
                interview_type VARCHAR(50) DEFAULT 'general',
                status VARCHAR(20) DEFAULT 'in_progress',
                created_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP,
                overall_score FLOAT
            )
        """)

        # Interview messages table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS interview_messages (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES interview_sessions(id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                question_number INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Interview feedback table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS interview_feedback (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES interview_sessions(id) ON DELETE CASCADE,
                user_id VARCHAR(255) NOT NULL,
                overall_score FLOAT,
                communication_score FLOAT,
                content_score FLOAT,
                confidence_score FLOAT,
                strengths JSONB,
                improvements JSONB,
                detailed_feedback TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Create indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_resumes_user ON user_resumes(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON interview_sessions(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user ON interview_feedback(user_id)")

    conn.commit()
    print("Interview prep tables initialized successfully")
