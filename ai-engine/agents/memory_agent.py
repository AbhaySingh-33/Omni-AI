from services.memory import get_history
from app.gemini import llm

def memory_agent(state):
    messages = state["messages"]
    query = messages[-1].content

    user_id = "default_user"  # later from auth

    history = get_history(user_id)

    history_text = "\n".join(
        [f"User: {m} | AI: {r}" for m, r in history]
    )

    prompt = f"""
You are a memory-aware AI.

Previous conversation:
{history_text}

Current question:
{query}
"""

    result = llm.invoke(prompt)
    content = result.content

    if isinstance(content, list):
        content = "".join([item.get("text", "") for item in content if isinstance(item, dict)])

    return {
        "messages": [("assistant", content)]
    }