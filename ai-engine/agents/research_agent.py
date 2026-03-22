from app.gemini import llm
from services.retriever import retrieve_context

def research_agent(state):
    messages = state["messages"]
    query = messages[-1].content

    context = retrieve_context(query)

    prompt = f"""
You are a research AI.

Use ONLY the given context to answer.

If context is empty, say "No data found".

Context:
{context}

Question:
{query}
"""

    result = llm.invoke(prompt)
    content = result.content

    if isinstance(content, list):
        content = "".join([item.get("text", "") for item in content if isinstance(item, dict)])

    return {
        "messages": [("assistant", content)]
    }