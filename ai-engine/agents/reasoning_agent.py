from app.dspy_module import QAModule, qa, qa_context

def reasoning_agent(state):
    messages = state["messages"]
    if not messages:
        return {"messages": [("assistant", "No query provided.")], "agent_used": "reasoning"}

    # Find the last user message to use as the query
    last_user_msg = next((m for m in reversed(messages) if m.type == "human" or m.type == "user"), None)
    current_query = last_user_msg.content if last_user_msg else messages[-1].content

    # --- Emotion-aware context injection ---
    emotion_ctx = state.get("emotion_context")
    emotion_prefix = ""
    if emotion_ctx and emotion_ctx.get("emotion") and emotion_ctx["emotion"] != "neutral":
        try:
            from emotion.prompts import get_emotion_context_for_dspy
            emotion_prefix = get_emotion_context_for_dspy(
                recommended_tone=emotion_ctx.get("recommended_tone", "supportive"),
                trend_summary=emotion_ctx.get("trend_summary", ""),
                emotion=emotion_ctx.get("emotion", ""),
                intensity=emotion_ctx.get("intensity", ""),
                is_crisis=emotion_ctx.get("is_crisis", False),
            )
        except Exception:
            emotion_prefix = ""

    if len(messages) <= 1 and not emotion_prefix:
        result = qa(question=current_query)
        return {"messages": [("assistant", result.answer)], "agent_used": "reasoning"}

    # Build context from conversation history + emotion awareness
    context_parts = []
    if emotion_prefix:
        context_parts.append(emotion_prefix)
    
    conv_context = "\n".join([f"{msg.type}: {msg.content}" for msg in messages if msg != last_user_msg])
    if conv_context:
        context_parts.append(conv_context)
    
    # If we only have emotion context and no conversation context, still use context-aware module
    context = "\n\n".join(context_parts) if context_parts else ""
    
    if context:
        result = qa_context(question=current_query, context=context)
    else:
        result = qa(question=current_query)

    return {
        "messages": [("assistant", result.answer)],
        "agent_used": "reasoning"
    }

