"""
Rule-Based Emotion Classifier
==============================
Sub-millisecond emotion detection using weighted keyword lexicon.
No ML model call — pure Python string matching.

Supports 8 emotion categories:
    joy, sadness, anger, fear, anxiety, stress, self_doubt, hopelessness

Optional: Drop a CSV at emotion/lexicon_custom.csv to extend/override.
Format: keyword,emotion,weight
"""

from __future__ import annotations

import csv
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class EmotionResult:
    """Result of emotion classification."""
    emotion: str              # primary detected emotion
    confidence: float         # 0.0 – 1.0
    intensity: str            # low / moderate / high / severe
    scores: Dict[str, float]  # all category scores (normalized)
    is_crisis: bool           # True for dangerous patterns
    raw_text_len: int = 0     # for analytics

    def to_dict(self) -> dict:
        return {
            "emotion": self.emotion,
            "confidence": round(self.confidence, 3),
            "intensity": self.intensity,
            "scores": {k: round(v, 3) for k, v in self.scores.items()},
            "is_crisis": self.is_crisis,
        }


# ---------------------------------------------------------------------------
# Crisis patterns — checked FIRST, hard-coded for safety
# ---------------------------------------------------------------------------

CRISIS_PATTERNS: List[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(want|going|plan(ning)?)\s+(to\s+)?(end|finish)\s+(it|my\s*life|everything)\b",
        r"\bgive\s+up\s+(everything|on\s+(life|myself|me))\b",
        r"\b(no|not?\s+any)\s+(reason|point|purpose)\s+(to|for)\s+(live|living|exist)\b",
        r"\b(kill|hurt|harm)\s+(myself|me)\b",
        r"\bsuicid(e|al)\b",
        r"\bself[\s\-]?harm\b",
        r"\bdon'?t\s+want\s+to\s+(live|exist|be\s+alive|be\s+here)\b",
        r"\bwish\s+i\s+(was|were)\s+(dead|gone|never\s+born)\b",
        r"\bnobody\s+(cares|would\s+(miss|notice))\b",
        r"\bend\s+(it\s+)?all\b",
        r"\bcan'?t\s+(take|handle|do)\s+(it|this)\s+(any\s*more|anymore)\b",
        r"\b(life|world)\s+(is\s+)?(meaningless|pointless|hopeless|not\s+worth)\b",
    ]
]


# ---------------------------------------------------------------------------
# Built-in Emotion Lexicon  (keyword -> (emotion, weight))
# ---------------------------------------------------------------------------

_BUILTIN_LEXICON: Dict[str, Tuple[str, float]] = {}

def _add(keywords: List[str], emotion: str, weight: float):
    for kw in keywords:
        _BUILTIN_LEXICON[kw.lower()] = (emotion, weight)


# -- Joy --
_add(["happy", "happiness", "glad", "excited", "amazing", "wonderful",
      "fantastic", "great", "awesome", "love", "loving", "joyful", "joy",
      "delighted", "thrilled", "ecstatic", "cheerful", "grateful",
      "thankful", "blessed", "optimistic", "hopeful", "proud",
      "accomplished", "satisfied", "content", "peaceful", "relieved",
      "inspired", "motivated", "energized", "celebrate", "celebrating",
      "fun", "enjoying", "enjoyed", "pleasure", "smile", "smiling",
      "laughing", "laugh", "bliss", "elated"], "joy", 0.7)

_add(["feeling good", "feel great", "so happy", "really excited",
      "best day", "on top of the world", "over the moon"], "joy", 0.9)

# -- Sadness --
_add(["sad", "sadness", "unhappy", "miserable", "heartbroken", "grief",
      "grieving", "mourning", "depressed", "depression", "melancholy",
      "sorrow", "sorrowful", "gloomy", "down", "feeling down", "low",
      "lonely", "loneliness", "alone", "isolated", "empty", "emptiness",
      "numb", "numbness", "crying", "cry", "tears", "tearful", "hurt",
      "hurting", "broken", "shattered", "devastated", "discouraged",
      "disappointed", "hopeless", "despair", "suffering", "pain",
      "painful", "aching", "heartache", "miss", "missing"], "sadness", 0.7)

_add(["deeply sad", "so depressed", "can't stop crying", "feel nothing",
      "completely alone", "no one understands", "utterly miserable",
      "drowning in sadness"], "sadness", 0.95)

# -- Anger --
_add(["angry", "anger", "furious", "enraged", "mad", "irritated",
      "annoyed", "frustrated", "frustration", "resentful", "resentment",
      "bitter", "bitterness", "outraged", "livid", "fuming", "hostile",
      "aggressive", "rage", "raging", "infuriated", "disgusted",
      "hate", "hatred", "despise", "loathe", "fed up"], "anger", 0.7)

_add(["so angry", "absolutely furious", "can't stand this",
      "sick of everything", "boiling with rage"], "anger", 0.9)

# -- Fear --
_add(["afraid", "fear", "scared", "terrified", "frightened", "panicked",
      "panic", "dread", "dreading", "horrified", "horror", "phobia",
      "paranoid", "paranoia", "nervous", "uneasy", "alarmed",
      "threatened", "vulnerable", "helpless", "trapped",
      "overwhelming", "overwhelmed"], "fear", 0.7)

_add(["absolutely terrified", "paralyzed with fear", "can't move",
      "shaking with fear", "so scared"], "fear", 0.9)

# -- Anxiety --
_add(["anxious", "anxiety", "worried", "worrying", "worry", "nervous",
      "restless", "tense", "tension", "on edge", "overthinking",
      "ruminating", "obsessing", "insecure", "insecurity", "uncertain",
      "uncertainty", "doubt", "doubtful", "apprehensive", "uneasy",
      "unsettled", "agitated", "jittery", "stressed out",
      "can't relax", "racing thoughts", "can't sleep", "insomnia",
      "sleepless", "panic attack", "hyperventilating"], "anxiety", 0.7)

_add(["constant anxiety", "crippling anxiety", "anxiety attack",
      "can't breathe", "chest tight", "losing control",
      "going crazy"], "anxiety", 0.95)

# -- Stress --
_add(["stressed", "stress", "pressure", "pressured", "burden",
      "burdened", "overloaded", "overworked", "exhausted", "exhaustion",
      "burnout", "burnt out", "burned out", "drained", "fatigued",
      "fatigue", "tired", "worn out", "stretched thin", "swamped",
      "drowning", "too much", "can't cope", "struggling",
      "overwhelm", "deadline", "deadlines"], "stress", 0.7)

_add(["completely burned out", "at breaking point", "can't take anymore",
      "falling apart", "so exhausted", "total burnout"], "stress", 0.9)

# -- Self-doubt --
_add(["worthless", "useless", "incompetent", "failure", "loser",
      "not good enough", "inadequate", "inferior", "imposter",
      "fraud", "stupid", "dumb", "pathetic", "can't do anything right",
      "no talent", "no skills", "waste of space", "burden to others",
      "don't deserve", "unworthy", "unlovable", "ugly",
      "self-doubt", "self doubt", "insecure", "hate myself",
      "not enough", "never enough", "always fail"], "self_doubt", 0.8)

_add(["completely worthless", "total failure", "everyone hates me",
      "nobody loves me", "i'm nothing", "piece of garbage",
      "waste of life", "shouldn't exist"], "self_doubt", 0.95)

# -- Hopelessness --
_add(["hopeless", "no hope", "give up", "giving up", "pointless",
      "meaningless", "nothing matters", "what's the point",
      "why bother", "no future", "no way out", "stuck forever",
      "never get better", "always be this way", "can't change",
      "done trying", "lost cause", "no escape", "trapped",
      "doomed", "cursed"], "hopelessness", 0.85)

_add(["completely hopeless", "no reason to go on", "everything is over",
      "nothing will ever change", "life is meaningless",
      "i want to disappear", "wish i could vanish"], "hopelessness", 0.95)


# ---------------------------------------------------------------------------
# CSV loader for custom lexicon
# ---------------------------------------------------------------------------

_CUSTOM_LEXICON_PATH = os.path.join(os.path.dirname(__file__), "lexicon_custom.csv")


def _load_custom_lexicon() -> Dict[str, Tuple[str, float]]:
    """Load custom keyword overrides from CSV if present."""
    if not os.path.isfile(_CUSTOM_LEXICON_PATH):
        return {}
    custom: Dict[str, Tuple[str, float]] = {}
    with open(_CUSTOM_LEXICON_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            kw = row.get("keyword", "").strip().lower()
            em = row.get("emotion", "").strip().lower()
            wt = float(row.get("weight", "0.7"))
            if kw and em:
                custom[kw] = (em, wt)
    return custom


def _get_merged_lexicon() -> Dict[str, Tuple[str, float]]:
    """Merge built-in + custom lexicon (custom wins on conflicts)."""
    merged = dict(_BUILTIN_LEXICON)
    merged.update(_load_custom_lexicon())
    return merged


# Cache the merged lexicon at module load
_LEXICON = _get_merged_lexicon()


def reload_lexicon():
    """Hot-reload the lexicon (e.g. after CSV update)."""
    global _LEXICON
    _LEXICON = _get_merged_lexicon()


# ---------------------------------------------------------------------------
# Core classifier
# ---------------------------------------------------------------------------

VALID_EMOTIONS = ["joy", "sadness", "anger", "fear", "anxiety",
                  "stress", "self_doubt", "hopelessness"]

NEGATIVE_EMOTIONS = {"sadness", "anger", "fear", "anxiety",
                     "stress", "self_doubt", "hopelessness"}


def _intensity_label(score: float) -> str:
    if score >= 0.8:
        return "severe"
    if score >= 0.6:
        return "high"
    if score >= 0.3:
        return "moderate"
    return "low"


def detect_emotion(text: str) -> EmotionResult:
    """
    Detect the primary emotion in *text*.

    Returns an EmotionResult with the top emotion, confidence,
    intensity level, all scores, and crisis flag.

    Runs in sub-millisecond time — no network calls.
    """
    if not text or not text.strip():
        return EmotionResult(
            emotion="neutral",
            confidence=0.0,
            intensity="low",
            scores={e: 0.0 for e in VALID_EMOTIONS},
            is_crisis=False,
            raw_text_len=0,
        )

    lower = text.lower().strip()

    # --- 1. Crisis check (always first) ---
    is_crisis = any(p.search(lower) for p in CRISIS_PATTERNS)

    # --- 2. Score accumulation ---
    scores: Dict[str, float] = {e: 0.0 for e in VALID_EMOTIONS}
    hit_count = 0

    # Sort lexicon keys by length descending so longer phrases match first
    for keyword, (emotion, weight) in sorted(
        _LEXICON.items(), key=lambda x: len(x[0]), reverse=True
    ):
        # Word-boundary-aware search for single words, substring for phrases
        if " " in keyword:
            if keyword in lower:
                scores[emotion] += weight
                hit_count += 1
        else:
            if re.search(rf"\b{re.escape(keyword)}\b", lower):
                scores[emotion] += weight
                hit_count += 1

    # --- 3. Normalize scores to 0-1 range ---
    max_score = max(scores.values()) if scores else 0.0
    if max_score > 0:
        for e in scores:
            scores[e] = min(scores[e] / (max_score * 1.2), 1.0)
        # Re-find max after normalization
        max_score = max(scores.values())

    # --- 4. Determine primary emotion ---
    if max_score == 0.0 and not is_crisis:
        return EmotionResult(
            emotion="neutral",
            confidence=0.0,
            intensity="low",
            scores=scores,
            is_crisis=False,
            raw_text_len=len(text),
        )

    if is_crisis:
        # Force hopelessness for crisis
        scores["hopelessness"] = max(scores["hopelessness"], 0.95)
        primary = "hopelessness"
        confidence = 0.95
    else:
        primary = max(scores, key=scores.get)  # type: ignore
        confidence = scores[primary]

    # Boost confidence if multiple keywords matched
    if hit_count >= 3:
        confidence = min(confidence * 1.15, 1.0)

    intensity = _intensity_label(confidence)

    # Crisis always gets severe
    if is_crisis:
        intensity = "severe"

    return EmotionResult(
        emotion=primary,
        confidence=round(confidence, 3),
        intensity=intensity,
        scores=scores,
        is_crisis=is_crisis,
        raw_text_len=len(text),
    )


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_cases = [
        ("I want to give up everything", "hopelessness", True),
        ("I'm feeling great today!", "joy", False),
        ("I've been so stressed about work lately", "stress", False),
        ("I'm really anxious about tomorrow", "anxiety", False),
        ("Nobody cares about me", "hopelessness", True),
        ("I feel so worthless and stupid", "self_doubt", False),
        ("I'm angry at everyone", "anger", False),
        ("I can't stop crying, I feel so alone", "sadness", False),
        ("Hello, how are you?", "neutral", False),
        ("I want to end it all", "hopelessness", True),
        ("Life is meaningless", "hopelessness", True),
    ]

    print("=" * 70)
    print("EMOTION CLASSIFIER — SELF-TEST")
    print("=" * 70)
    passed = 0
    for text, expected_emotion, expected_crisis in test_cases:
        result = detect_emotion(text)
        ok_emotion = result.emotion == expected_emotion
        ok_crisis = result.is_crisis == expected_crisis
        status = "✓" if (ok_emotion and ok_crisis) else "✗"
        if status == "✓":
            passed += 1
        print(f"\n{status} \"{text}\"")
        print(f"  Expected: {expected_emotion} (crisis={expected_crisis})")
        print(f"  Got:      {result.emotion} (crisis={result.is_crisis}) "
              f"conf={result.confidence} intensity={result.intensity}")
    print(f"\n{'=' * 70}")
    print(f"Results: {passed}/{len(test_cases)} passed")
    print("=" * 70)
