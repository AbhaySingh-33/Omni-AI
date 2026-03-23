from app.dspy_module import QAModule, qa, qa_context

def reasoning_agent(state):
    messages = state["messages"]
    if not messages:
        return {"messages": [("assistant", "No query provided.")]}

    current_query = messages[-1].content

    # If this is the standalone first step
    if len(messages) <= 1:
        result = qa(question=current_query)
        return {"messages": [("assistant", result.answer)]}

    # If part of a conversation loop, use context
    context = "\n".join([f"{msg.type}: {msg.content}" for msg in messages[:-1]])
    
    # We use the context-aware module
    result = qa_context(question=current_query, context=context)

    return {
        "messages": [("assistant", result.answer)]
    }
