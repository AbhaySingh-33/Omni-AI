from app.gemini import llm
import re

# Keywords that always need live web search regardless of LLM routing
LIVE_DATA_KEYWORDS = [
    "ipl", "cricket", "match", "score", "live", "today", "tonight", "current",
    "weather", "news", "latest", "2024", "2025", "2026", "2027",
    "who won", "who is", "price", "stock", "election", "result", "schedule",
    "fixture", "standings", "ranking", "trending"
]

# Keywords that always route to research (RAG) agent
RESEARCH_KEYWORDS = [
    "document", "pdf", "file", "uploaded", "according to", "based on",
    "in the document", "from the file", "what does it say", "summarize the",
    "extract", "find in", "in the story", "in the book", "who said",
    "what happened", "chapter", "plot", "novel", "character", "passage"
]

def router_agent(state):
    messages = state["messages"]
    query = messages[-1].content.lower()

    # Fast-path: confirmation replies → always tools
    if query.strip() in ("allow", "deny"):
        return {"next": "tools"}

    # Fast-path: if query contains live data keywords → always tools
    if any(kw in query for kw in LIVE_DATA_KEYWORDS):
        return {"next": "tools"}

    # Fast-path: document/PDF/story questions → always research
    if any(kw in query for kw in RESEARCH_KEYWORDS):
        return {"next": "research"}

    # Sanitize user input before injecting into LLM prompt
    safe_content = messages[-1].content.replace("{", "{{").replace("}", "}}")

    prompt = f"""You are a router. Classify the user query into exactly one category.

Categories:
- memory    → asking about past conversations or what was said before
- reasoning → general knowledge, explanations, coding help, opinions
- research  → questions about documents or data the user has uploaded
- tools     → anything that requires taking an action or fetching live data:
              * create/read/write/list files
              * run terminal/shell commands
              * web search, weather, news
              * math calculations

IMPORTANT: If the user wants to DO something (create, write, run, search, calculate) → tools

Respond with ONLY one word: memory / reasoning / research / tools

Query: {safe_content}"""

    result = llm.invoke(prompt)
    content = result.content

    if isinstance(content, list):
        content = "".join([item.get("text", "") for item in content if isinstance(item, dict)])

    match = re.search(r"\b(memory|reasoning|research|tools)\b", content.strip().lower())
    route = match.group(1) if match else "reasoning"

    return {"next": route}
