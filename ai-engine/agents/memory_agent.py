from services.memory import get_history, get_summary
from app.gemini import llm

def memory_agent(state):
    messages = state["messages"]
    query = messages[-1].content
    user_id = state.get("user_id", "default_user")

    summary = get_summary(user_id)
    history = get_history(user_id)
    history_text = "\n".join([f"User: {m}\nAI: {r}" for m, r in history])

    summary_section = f"Long-term memory summary:\n{summary}\n\n" if summary else ""
    history_section = f"Recent conversation:\n{history_text}\n\n" if history_text else ""

    prompt = f"""You are a memory-aware AI assistant.
Use the information below to answer the user's question accurately.

{summary_section}{history_section}Current question:
{query}

Answer based on what you know about this user from the memory above:"""

    result = llm.invoke(prompt)
    content = result.content

    if isinstance(content, list):
        content = "".join([item.get("text", "") for item in content if isinstance(item, dict)])

    return {"messages": [("assistant", content)], "agent_used": "memory"}
