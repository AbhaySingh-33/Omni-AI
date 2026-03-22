from app.gemini import llm

def router_agent(state):
    messages = state["messages"]

    prompt = f"""
You are a router AI.

Rules:
- If user asks about past conversation → memory
- If user asks general question → reasoning
- If user asks factual/external info → research
- If user wants action → tools

Respond ONLY with:
reasoning / research / tools / memory

User Query:
{messages[-1].content}
"""

    result = llm.invoke(prompt)
    content = result.content
    
    if isinstance(content, list):
        content = "".join([item.get("text", "") for item in content if isinstance(item, dict)])
    
    response = content.strip().lower()

    return {
        "next": response
    }