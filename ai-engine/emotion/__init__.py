"""
Emotion Detection & Mental Health Tracking Engine
==================================================
Zero-latency rule-based emotion classifier with risk assessment,
trend tracking, and emotion-aware LLM prompt generation.

Public API:
    detect_emotion(text)        -> EmotionResult
    assess_risk(user_id, er)    -> RiskAssessment
    get_emotion_prompt(ctx)     -> str
"""

from emotion.classifier import detect_emotion, EmotionResult
from emotion.risk_engine import assess_risk, RiskAssessment
from emotion.prompts import get_emotion_prompt

__all__ = [
    "detect_emotion",
    "EmotionResult",
    "assess_risk",
    "RiskAssessment",
    "get_emotion_prompt",
]
