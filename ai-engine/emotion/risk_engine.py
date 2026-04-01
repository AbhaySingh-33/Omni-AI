"""
Risk Assessment Engine
=======================
Evaluates mental health risk based on current emotion + historical trend.
Queries the emotion store for recent history and calculates:
  - Trend direction (improving / stable / worsening)
  - Escalation score
  - Consecutive negative days
  - Overall risk level (low / moderate / high / critical)
  - Recommended response tone
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from emotion.classifier import EmotionResult, NEGATIVE_EMOTIONS
from emotion.emotion_store import get_recent_emotions, save_alert


@dataclass
class RiskAssessment:
    """Output of the risk engine."""
    risk_level: str             # low / moderate / high / critical
    trend: str                  # improving / stable / worsening
    escalation_score: float     # 0.0 – 1.0
    consecutive_negative: int   # streak of negative emotion entries
    recommended_tone: str       # supportive / consoling / motivational / crisis_intervention
    trend_summary: str          # human-readable trend description for LLM prompt
    trigger_alert: bool         # whether to create an alert

    def to_dict(self) -> dict:
        return {
            "risk_level": self.risk_level,
            "trend": self.trend,
            "escalation_score": round(self.escalation_score, 3),
            "consecutive_negative": self.consecutive_negative,
            "recommended_tone": self.recommended_tone,
            "trend_summary": self.trend_summary,
            "trigger_alert": self.trigger_alert,
        }


# ---------------------------------------------------------------------------
# Tone mapping
# ---------------------------------------------------------------------------

_TONE_MAP = {
    "low": "supportive",
    "moderate": "supportive",
    "high": "consoling",
    "critical": "crisis_intervention",
}

_TONE_OVERRIDE = {
    # If user was improving → motivational
    "improving": "motivational",
}


# ---------------------------------------------------------------------------
# Core risk assessment
# ---------------------------------------------------------------------------

def assess_risk(user_id: str, emotion_result: EmotionResult) -> RiskAssessment:
    """
    Assess user risk given the current emotion and their history.

    This is called on every message but the DB query is lightweight
    (fetches at most 7 rows with an indexed query).
    """

    # --- 1. Immediate crisis check ---
    if emotion_result.is_crisis:
        summary = ("⚠️ Crisis detected. The user expressed something deeply "
                   "concerning. They need immediate, genuine human warmth.")
        ra = RiskAssessment(
            risk_level="critical",
            trend="worsening",
            escalation_score=1.0,
            consecutive_negative=0,
            recommended_tone="crisis_intervention",
            trend_summary=summary,
            trigger_alert=True,
        )
        # Fire alert
        save_alert(
            user_id, "crisis", "critical",
            f"Crisis detected: emotion={emotion_result.emotion}, "
            f"confidence={emotion_result.confidence}"
        )
        return ra

    # --- 2. Fetch recent history ---
    history = get_recent_emotions(user_id, limit=7)

    if not history:
        # First-time user, no history
        tone = _TONE_MAP.get(
            "moderate" if emotion_result.emotion in NEGATIVE_EMOTIONS else "low",
            "supportive"
        )
        return RiskAssessment(
            risk_level="low",
            trend="stable",
            escalation_score=0.0,
            consecutive_negative=0,
            recommended_tone=tone,
            trend_summary="",
            trigger_alert=False,
        )

    # --- 3. Analyze trend ---
    neg_scores = []
    consecutive_negative = 0
    current_streak = 0

    for entry in history:
        is_neg = entry["emotion"] in NEGATIVE_EMOTIONS
        if is_neg:
            current_streak += 1
            neg_scores.append(entry.get("confidence", 0.5))
        else:
            current_streak = 0

    consecutive_negative = current_streak

    # Current message extends the streak
    if emotion_result.emotion in NEGATIVE_EMOTIONS:
        consecutive_negative += 1
        neg_scores.append(emotion_result.confidence)

    # Calculate escalation score (are negative emotions getting WORSE?)
    escalation_score = 0.0
    trend = "stable"

    if len(neg_scores) >= 2:
        # Compare first half vs second half averages
        mid = len(neg_scores) // 2
        first_half = sum(neg_scores[:mid]) / max(mid, 1)
        second_half = sum(neg_scores[mid:]) / max(len(neg_scores) - mid, 1)
        diff = second_half - first_half

        if diff > 0.1:
            trend = "worsening"
            escalation_score = min(diff * 2, 1.0)
        elif diff < -0.1:
            trend = "improving"
            escalation_score = 0.0
        else:
            trend = "stable"
            escalation_score = max(0.0, diff)
    elif len(neg_scores) == 1:
        escalation_score = neg_scores[0] * 0.3

    # --- 4. Calculate overall risk level ---
    risk_score = 0.0

    # Factor 1: Current emotion intensity
    intensity_map = {"low": 0.1, "moderate": 0.3, "high": 0.6, "severe": 0.9}
    risk_score += intensity_map.get(emotion_result.intensity, 0.1) * 0.4

    # Factor 2: Escalation
    risk_score += escalation_score * 0.3

    # Factor 3: Consecutive negative streak
    streak_factor = min(consecutive_negative / 5, 1.0)
    risk_score += streak_factor * 0.3

    # Determine risk level
    if risk_score >= 0.7:
        risk_level = "critical"
    elif risk_score >= 0.5:
        risk_level = "high"
    elif risk_score >= 0.3:
        risk_level = "moderate"
    else:
        risk_level = "low"

    # --- 5. Determine recommended tone ---
    if trend == "improving" and risk_level in ("low", "moderate"):
        recommended_tone = "motivational"
    else:
        recommended_tone = _TONE_MAP.get(risk_level, "supportive")

    # --- 6. Build trend summary for LLM ---
    trend_summary = _build_trend_summary(
        history, emotion_result, trend, consecutive_negative
    )

    # --- 7. Alert check ---
    trigger_alert = False
    if risk_level in ("high", "critical"):
        trigger_alert = True
        save_alert(
            user_id, "risk_escalation", risk_level,
            f"Risk escalating: trend={trend}, streak={consecutive_negative}, "
            f"current={emotion_result.emotion}"
        )

    return RiskAssessment(
        risk_level=risk_level,
        trend=trend,
        escalation_score=round(escalation_score, 3),
        consecutive_negative=consecutive_negative,
        recommended_tone=recommended_tone,
        trend_summary=trend_summary,
        trigger_alert=trigger_alert,
    )


def _build_trend_summary(
    history: List[Dict],
    current: EmotionResult,
    trend: str,
    streak: int,
) -> str:
    """Build a human-readable trend summary to inject into LLM prompt."""
    if not history:
        return ""

    parts = []

    # Recent emotion sequence
    recent_emotions = [h["emotion"] for h in history[-5:]]
    if recent_emotions:
        parts.append(
            f"User's recent emotional states: {' → '.join(recent_emotions)} → {current.emotion} (now)"
        )

    # Trend
    if trend == "worsening":
        parts.append(
            "⚠️ Their emotional state has been WORSENING over recent interactions."
        )
    elif trend == "improving":
        parts.append(
            "Their emotional state has been improving recently — they're making progress."
        )

    # Streak
    if streak >= 3:
        parts.append(
            f"They have shown negative emotions for {streak} consecutive interactions."
        )

    return " ".join(parts)
