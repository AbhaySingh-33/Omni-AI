from app.dspy_module import QAModule, qa, qa_context

def reasoning_agent(state):
    messages = state["messages"]
    if not messages:
        return {"messages": [("assistant", "No query provided.")], "agent_used": "reasoning"}

    # Find the last user message to use as the query
    last_user_msg = next((m for m in reversed(messages) if m.type == "human" or m.type == "user"), None)
    current_query = last_user_msg.content if last_user_msg else messages[-1].content

    if len(messages) <= 1:
        result = qa(question=current_query)
        return {"messages": [("assistant", result.answer)], "agent_used": "reasoning"}

    # If part of a conversation loop, use context
    context = "\n".join([f"{msg.type}: {msg.content}" for msg in messages if msg != last_user_msg])
    
    # We use the context-aware module
    result = qa_context(question=current_query, context=context)

    return {
        "messages": [("assistant", result.answer)],
        "agent_used": "reasoning"
    }
