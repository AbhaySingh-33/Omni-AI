from app.gemini import llm

def reasoning_agent(state):
    messages = state["messages"]

    result = llm.invoke(messages)
    content = result.content

    if isinstance(content, list):
        content = "".join([item.get("text", "") for item in content if isinstance(item, dict)])

    return {
        "messages": [("assistant", content)]
    }