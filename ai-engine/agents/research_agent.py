from app.gemini import llm
from services.retriever import retrieve_context
from services.kg import query_kg, format_kg_context


def research_agent(state):
    messages = state["messages"]
    query = messages[-1].content
    user_id = state.get("user_id", "default_user")

    context = retrieve_context(query, user_id)

    kg_context = None
    try:
        kg_rows = query_kg(query, user_id)
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
