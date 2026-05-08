import json
import re
from typing import Dict, List, Optional, TypedDict

from langgraph.graph import START, END, StateGraph

from app.gemini import llm
from legal_rag.prompts import QUERY_CLASSIFIER_PROMPT
from legal_rag.neo4j_store import LegalGraphStore
from legal_rag.retriever import LegalGraphRetriever, intent_default_node_types
from legal_rag.web_tools import search_legal_act


class LegalRAGState(TypedDict):
    user_id: str
    question: str
    doc_id: Optional[str]
    intent: str
    query_terms: List[str]
    rewritten_query: str
    expanded_queries: List[str]
    citations: List[str]
    event_focus: List[str]
    preferred_node_types: List[str]
    preferred_sections: List[str]
    candidate_nodes: List[Dict]
    expanded: Dict
    missing_acts: List[str]
    fetched_acts: List[Dict]
    answer: str


def _extract_json(text: str) -> Optional[Dict]:
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def plan_query(state: LegalRAGState) -> LegalRAGState:
    prompt = f"""
{QUERY_CLASSIFIER_PROMPT}

Question: {state['question']}
"""
    try:
        result = llm.invoke(prompt)
        payload = _extract_json(getattr(result, "content", "") or "") or {}
        intent = str(payload.get("intent", "summary")).strip().lower()
        if intent not in {
            "issue", "facts", "statute", "procedure", "reasoning", "holding", "timeline", "relief", "summary"
        }:
            intent = "summary"
        rewritten_query = str(payload.get("rewritten_query", "")).strip()
        expanded_queries = [str(q).strip() for q in payload.get("query_variants", []) if str(q).strip()]
        citations = [str(c).strip() for c in payload.get("citations", []) if str(c).strip()]
        event_focus = [str(e).strip() for e in payload.get("event_focus", []) if str(e).strip()]
        preferred_node_types = [str(n).lower().strip() for n in payload.get("target_node_types", []) if str(n).strip()]
    except Exception:
        intent = "summary"
        rewritten_query = ""
        expanded_queries = []
        citations = []
        event_focus = []
        preferred_node_types = []

    terms = [t.lower() for t in re.findall(r"[A-Za-z0-9\.\-]{3,}", f"{rewritten_query} {' '.join(expanded_queries)}")][:16]

    if not terms:
        terms = [t.lower() for t in re.findall(r"[A-Za-z0-9\.\-]{3,}", state["question"])][:12]

    if not rewritten_query:
        rewritten_query = state["question"]

    if not expanded_queries:
        expanded_queries = [
            rewritten_query,
            state["question"],
            f"pinpoint legal basis for {state['question']}",
            f"procedural findings for {state['question']}",
        ]

    if not preferred_node_types:
        preferred_node_types = intent_default_node_types(intent)

    state["intent"] = intent
    state["query_terms"] = terms
    state["rewritten_query"] = rewritten_query
    state["expanded_queries"] = expanded_queries[:5]
    state["citations"] = citations[:10]
    state["event_focus"] = event_focus[:8]
    state["preferred_node_types"] = preferred_node_types[:8]
    state["preferred_sections"] = preferred_node_types[:6]
    return state


def find_candidates(state: LegalRAGState) -> LegalRAGState:
    retriever = LegalGraphRetriever()
    candidates = retriever.find_candidate_nodes(
        user_id=state["user_id"],
        question=state.get("rewritten_query") or state["question"],
        doc_id=state.get("doc_id"),
        query_variants=state.get("expanded_queries", []),
        preferred_sections=state.get("preferred_sections", []),
        preferred_node_types=state.get("preferred_node_types", []),
        citations=state.get("citations", []),
    )
    state["candidate_nodes"] = candidates
    return state


def expand_graph_context(state: LegalRAGState) -> LegalRAGState:
    retriever = LegalGraphRetriever()
    node_ids = [n.get("node_id") for n in state.get("candidate_nodes", []) if n.get("node_id")]
    state["expanded"] = retriever.expand_context(state["user_id"], node_ids)
    return state


def detect_missing_act_descriptions(state: LegalRAGState) -> LegalRAGState:
    missing: List[str] = []
    for act in state.get("expanded", {}).get("acts", []):
        if not (act.get("description") or "").strip() and act.get("name"):
            missing.append(act["name"])

    # Also include external references that may not yet exist as act nodes.
    for ref in state.get("expanded", {}).get("references", []):
        if ref.get("ref_type") == "external_act" and ref.get("target_label"):
            if ref["target_label"] not in missing:
                missing.append(ref["target_label"])

    state["missing_acts"] = missing[:3]
    return state


def should_fetch_web(state: LegalRAGState) -> str:
    return "fetch_web" if state.get("missing_acts") else "answer"


def fetch_web_definitions(state: LegalRAGState) -> LegalRAGState:
    store = LegalGraphStore()
    fetched: List[Dict] = []
    for act_name in state.get("missing_acts", []):
        try:
            result = search_legal_act(act_name)
            description = (result.get("description") or "").strip()
            if description:
                store.update_act_description(
                    user_id=state["user_id"],
                    act_name=act_name,
                    description=description,
                    source_url=result.get("source_url", ""),
                )
                fetched.append(result)
        except Exception:
            continue

    state["fetched_acts"] = fetched

    # Refresh expanded context so the answer stage sees newly filled descriptions.
    retriever = LegalGraphRetriever(store=store)
    node_ids = [n.get("node_id") for n in state.get("candidate_nodes", []) if n.get("node_id")]
    state["expanded"] = retriever.expand_context(state["user_id"], node_ids)
    return state


def generate_answer(state: LegalRAGState) -> LegalRAGState:
    retriever = LegalGraphRetriever()
    context = retriever.format_context(state.get("expanded", {}))

    prompt = f"""
You are a legal assistant answering ONLY from provided context.
If context is insufficient, explicitly say what is missing.
Include page references when available.
When legal citations are requested, cite the exact section/article/rule text that appears in context.
Do not infer facts not supported by context lines.

Question:
{state['question']}

Detected intent:
{state.get('intent', 'summary')}

Context:
{context}
"""

    try:
        result = llm.invoke(prompt)
        state["answer"] = (getattr(result, "content", "") or "").strip()
    except Exception as exc:
        state["answer"] = f"Could not generate answer due to model error: {exc}"

    if not state["answer"]:
        state["answer"] = "No answer generated from current legal graph context."

    return state


def build_legal_agent_graph():
    graph = StateGraph(LegalRAGState)

    graph.add_node("plan", plan_query)
    graph.add_node("find", find_candidates)
    graph.add_node("expand", expand_graph_context)
    graph.add_node("missing", detect_missing_act_descriptions)
    graph.add_node("fetch_web", fetch_web_definitions)
    graph.add_node("answer", generate_answer)

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "find")
    graph.add_edge("find", "expand")
    graph.add_edge("expand", "missing")
    graph.add_conditional_edges("missing", should_fetch_web, {"fetch_web": "fetch_web", "answer": "answer"})
    graph.add_edge("fetch_web", "answer")
    graph.add_edge("answer", END)

    return graph.compile()
