from app.gemini import llm
from services.retriever import retrieve_context
from services.kg import query_kg, format_kg_context
import concurrent.futures


def research_agent(state):
    messages = state["messages"]
    query = messages[-1].content
    user_id = state.get("user_id", "default_user")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        context_future = executor.submit(retrieve_context, query, user_id)
        kg_future = executor.submit(query_kg, query, user_id)

        try:
            context = context_future.result(timeout=2.5)
        except Exception:
            context = None

        kg_context = None
        try:
            kg_rows = kg_future.result(timeout=1.0)
            kg_context = format_kg_context(kg_rows)
        except Exception:
            kg_context = None

    prompt = f"""
You are a research AI.

Use ONLY the given context to answer.

If both contexts are empty, say "No data found in your documents.".

Knowledge Graph Context:
{kg_context if kg_context else "No relevant entities found"}

Document Context:
{context if context else "No document chunks found"}

Question:
{query}
"""

    result = llm.invoke(prompt)
    content = result.content

    if isinstance(content, list):
        content = "".join([item.get("text", "") for item in content if isinstance(item, dict)])

    return {"messages": [("assistant", content)], "agent_used": "research"}
