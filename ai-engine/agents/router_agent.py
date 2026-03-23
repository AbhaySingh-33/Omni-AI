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

MAX_ITERATIONS = 5

def router_agent(state):
    messages = state["messages"]
    iterations = state.get("iterations", 0)
    
    # Safety Check: Loop Limit
    if iterations >= MAX_ITERATIONS:
        return {"next": "finish"}

    last_message = messages[-1]
    last_content = last_message.content.lower().strip()

    # --- STOPPING CONDITIONS ---

    # 1. User Confirmation Request (from tool_agent)
    # If the last message asks for confirmation, we MUST stop to let the user reply.
    if "confirm" in last_content and ("allow" in last_content or "deny" in last_content):
        return {"next": "finish"}

    # 2. User says "allow" or "deny" -> Route back to tools immediately
    if last_message.type == "human" and last_content in ("allow", "deny"):
        return {"next": "tools", "iterations": 1}

    # --- FIRST STEP LOGIC (User just spoke) ---
    if last_message.type == "human" and iterations == 0:
        # Fast-path: live data -> tools
        if any(kw in last_content for kw in LIVE_DATA_KEYWORDS):
            return {"next": "tools", "iterations": 1}

        # Fast-path: documents -> research
        if any(kw in last_content for kw in RESEARCH_KEYWORDS):
            return {"next": "research", "iterations": 1}

        # LLM Classification
        prompt = f"""You are a router. Classify the user query into exactly one category.

Categories:
- memory    → asking about past conversations
- reasoning → general knowledge, explanations, coding help
- research  → questions about documents/files
- tools     → actions (create/read/write/run), search, math

Query: {last_content}

Respond with ONLY one word: memory / reasoning / research / tools"""
        
        result = llm.invoke(prompt)
        content = result.content.strip().lower()
        match = re.search(r"\b(memory|reasoning|research|tools)\b", content)
        route = match.group(1) if match else "reasoning"
        return {"next": route, "iterations": 1}

    # --- SUPERVISOR LOGIC (Agent just spoke) ---
    # The previous agent has finished. Do we need another step?
    
    # If the last step was effective (e.g. tool output), maybe we are done or need reasoning.
    # We ask the LLM to decide.

    prompt = f"""You are a Supervisor Agent. A worker agent has just performed a task.
    Decide what to do next.

    Conversation History:
    {messages[-2].content if len(messages) > 1 else ''}
    
    Last Output (from Worker):
    {last_content}

    Options:
    - finish    → The user's request is fully satisfied.
    - reasoning → Need to explain, summarize, or format the result.
    - research  → Need to look up documents.
    - tools     → Need to perform another action (search, file op).
    - memory    → Need to check memory.

    CRITICAL: 
    - If the last output is an answer to the user, valid and complete, choose "finish".
    - If the last output is a tool result (e.g. weather data), choose "reasoning" to explain it to the user.
    - Do NOT loop back to the SAME agent unless absolutely necessary.

    Respond with ONLY one word."""

    result = llm.invoke(prompt)
    content = result.content.strip().lower()
    
    match = re.search(r"\b(finish|reasoning|research|tools|memory)\b", content)
    route = match.group(1) if match else "finish"

    return {"next": route, "iterations": 1}
