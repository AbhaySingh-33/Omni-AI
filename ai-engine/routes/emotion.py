"""
Emotion Analytics API Endpoints
=================================
Provides authenticated endpoints for:
  - /emotion/history    — 30-day emotion history
  - /emotion/trend      — 7-day trend data for charts
  - /emotion/alerts     — active unacknowledged alerts
  - /emotion/analytics  — full dashboard payload
  - /emotion/alerts/{id}/acknowledge — mark alert as read
"""

from fastapi import APIRouter, Depends, Path
from app.auth import get_current_user
from emotion.emotion_store import (
    get_emotion_history,
    get_emotion_trend,
    get_active_alerts,
    get_user_analytics,
    acknowledge_alert,
)

router = APIRouter(prefix="/emotion", tags=["emotion"])


@router.get("/history")
def emotion_history(days: int = 30, user=Depends(get_current_user)):
    """Get daily emotion history for the last N days."""
    return {"history": get_emotion_history(user["user_id"], days=days)}


@router.get("/trend")
def emotion_trend(days: int = 7, user=Depends(get_current_user)):
    """Get detailed emotion trend data for charts."""
    return {"trend": get_emotion_trend(user["user_id"], days=days)}


@router.get("/alerts")
def emotion_alerts(user=Depends(get_current_user)):
    """Get active (unacknowledged) alerts."""
    return {"alerts": get_active_alerts(user["user_id"])}


@router.get("/analytics")
def emotion_analytics(user=Depends(get_current_user)):
    """Full analytics payload: current state + history + trend + alerts."""
    return get_user_analytics(user["user_id"])


@router.post("/alerts/{alert_id}/acknowledge")
def ack_alert(alert_id: int = Path(...), user=Depends(get_current_user)):
    """Mark an alert as acknowledged."""
    acknowledge_alert(alert_id)
    return {"status": "acknowledged"}
