"""Research agent — answers questions from uploaded documents.

Uses the hybrid retriever (BM25 + Vector with RRF fusion) so that exact
numbers, benchmark metrics, model names, and acronyms are matched reliably.
The prompt explicitly instructs the LLM to preserve exact values verbatim.
"""

from app.gemini import llm
from app.llm_utils import call_with_retry
from services.retriever import hybrid_retrieve
from services.kg import query_kg, format_kg_context
import concurrent.futures


_RESEARCH_PROMPT = """\
You are a precise research assistant. Your job is to answer the user's question
using ONLY the retrieved context below. Follow these rules strictly:

## Rules
1. **Quote exact values.** When the context contains specific numbers,
   percentages, dates, scores, or measurements, reproduce them EXACTLY as
   written. Do NOT round, paraphrase, or approximate.
2. **Preserve technical terms.** Model names (e.g. GPT-4, BERT-large),
   acronyms (e.g. MMLU, BLEU, F1), framework names, and version numbers
   must appear verbatim.
3. **Cite sources.** Reference the chunk filename when relevant, e.g.
   "According to [paper.pdf]...".
4. **Say "I couldn't find that information in your documents"** if neither the
   document context nor the knowledge graph context contains the answer.
   Never fabricate facts.
5. **Be concise.** Answer directly; avoid unnecessary preamble.

## Knowledge Graph Context
{kg_context}

## Document Context (Hybrid BM25 + Semantic Search)
{doc_context}

## User Question
{query}

Answer:"""


def research_agent(state):
    messages = state["messages"]
    query = messages[-1].content
    user_id = state.get("user_id", "default_user")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        context_future = executor.submit(hybrid_retrieve, query, user_id)
        kg_future = executor.submit(query_kg, query, user_id)

        try:
            context = context_future.result(timeout=6.0)
        except Exception:
            context = None

        kg_context = None
        try:
            kg_rows = kg_future.result(timeout=2.0)
            kg_context = format_kg_context(kg_rows)
        except Exception:
            kg_context = None

    prompt = _RESEARCH_PROMPT.format(
        kg_context=kg_context if kg_context else "No relevant entities found.",
        doc_context=context if context else "No document chunks found.",
        query=query,
    )

    result = call_with_retry(llm.invoke, prompt)
    content = result.content

    if isinstance(content, list):
        content = "".join([item.get("text", "") for item in content if isinstance(item, dict)])

    return {"messages": [("assistant", content)], "agent_used": "research"}
