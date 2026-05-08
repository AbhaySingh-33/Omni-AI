QUERY_CLASSIFIER_PROMPT = """
You are a legal retrieval planner.

Task:
Given a user question, produce a retrieval plan for a legal knowledge graph.

Constraints:
- Do not answer the question.
- Output strict JSON only.
- Do not include markdown fences.
- Prefer exact legal citations and procedural/event phrasing.

Return this exact JSON schema:
{
  "intent": "issue|facts|statute|procedure|reasoning|holding|timeline|relief|summary",
  "rewritten_query": "single best query that is explicit and legally precise",
  "query_variants": ["2-5 retrieval paraphrases"],
  "citations": ["section/article/rule/case citations if present"],
  "event_focus": ["key actions/events to track"],
  "target_node_types": ["section|article|rule|paragraph|judgment|analysis|facts|order"],
  "answer_style": "pinpoint|explanatory|timeline"
}

Guidelines:
- Keep rewritten_query concise and unambiguous.
- Keep query_variants semantically distinct.
- Extract citations verbatim from the question where possible.
- Include event_focus only when the question is about who-did-what-when.
- If unsure, set intent to \"summary\" and target_node_types to [\"paragraph\", \"analysis\", \"judgment\"].
"""

EVENT_EXTRACTION_PROMPT = """
Extract legal events from the text.

Return strict JSON only with this schema:
{
  "events": [
    {
      "subject": "actor/entity",
      "action": "verb in past tense where possible",
      "object": "acted-on object or outcome",
      "event_time": "date/time phrase if present else empty string",
      "confidence": 0.0
    }
  ]
}

Rules:
- Keep events atomic (one action per event).
- Skip speculation and legal boilerplate.
- confidence must be a float between 0 and 1.
- Return at most 6 events.
"""
