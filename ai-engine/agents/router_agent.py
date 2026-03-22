from app.gemini import llm
import re

def router_agent(state):
    messages = state["messages"]

    prompt = f"""You are a router. Classify the user query into exactly one category.

Categories:
- memory     → asking about past conversations or what was said before
- reasoning  → math, logic, coding, general knowledge questions
- research   → questions about documents or data the user has uploaded
- tools      → anything requiring live/real-time data (weather, news, search, calculations)

Respond with ONLY one word: memory / reasoning / research / tools

Query: {messages[-1].content}"""

    result = llm.invoke(prompt)
    content = result.content

    if isinstance(content, list):
        content = "".join([item.get("text", "") for item in content if isinstance(item, dict)])

    match = re.search(r"\b(memory|reasoning|research|tools)\b", content.strip().lower())
    route = match.group(1) if match else "reasoning"

    return {"next": route}
