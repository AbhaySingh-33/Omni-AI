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

# Keywords that route to interview agent
INTERVIEW_KEYWORDS = [
    "interview", "resume", "cv", "job application", "job search", "career",
    "mock interview", "practice interview", "interview question", "behavioral question",
    "technical interview", "hire", "hiring", "job offer", "prepare for interview",
    "interview prep", "interview tips", "improve resume", "create resume",
    "cover letter", "salary negotiation", "job hunt", "recruitment"
]
# Simple greetings and generic words that shouldn't require LLM routing
GREETING_KEYWORDS = [
    "hi", "hello", "hey", "good morning", "good evening", "how are you", 
    "what's up", "who are you", "help"
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
        # Fast-path: documents -> research
        if any(kw in last_content for kw in RESEARCH_KEYWORDS):
            return {"next": "research", "iterations": 1}

        # Fast-path: live data -> tools
        if any(kw in last_content for kw in LIVE_DATA_KEYWORDS):
            return {"next": "tools", "iterations": 1}

        # Fast-path: interview/career queries -> interview
        if any(kw in last_content for kw in INTERVIEW_KEYWORDS):
            return {"next": "interview", "iterations": 1}
            
        # Fast-path: simple greetings -> reasoning
        if last_content in GREETING_KEYWORDS:
            return {"next": "reasoning", "iterations": 1}

        # LLM Classification
        prompt = f"""You are a router. Classify the user query into exactly one category.

Categories:
- memory    → asking about past conversations
- reasoning → general knowledge, explanations, coding help
- research  → questions about documents/files
- tools     → actions (create/read/write/run), search, math
- interview → job search, resume, interview prep, career advice, mock interviews

Query: {last_content}

Respond with ONLY one word: memory / reasoning / research / tools / interview"""

        result = llm.invoke(prompt)
        content = result.content.strip().lower()
        match = re.search(r"\b(memory|reasoning|research|tools|interview)\b", content)
        route = match.group(1) if match else "reasoning"
        return {"next": route, "iterations": 1}

    # --- SUPERVISOR LOGIC (Agent just spoke) ---
    # Retrieve the state to see which agent just answered
    agent_used = state.get("agent_used", "")

    # If the active agent is designed to provide direct answers, we don't need the LLM to tell us to finish.
    # This optimization cuts response times by skipping unnecessary supervisor LLM calls.
    if agent_used in ("reasoning", "research", "memory", "interview"):
        return {"next": "finish", "iterations": 1}

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
    - interview → Need interview/career help.

    CRITICAL:
    - If the last output is an answer to the user, valid and complete, choose "finish".
    - If the last output is a tool result (e.g. weather data), choose "reasoning" to explain it to the user.
    - Do NOT loop back to the SAME agent unless absolutely necessary.

    Respond with ONLY one word."""

    result = llm.invoke(prompt)
    content = result.content.strip().lower()

    match = re.search(r"\b(finish|reasoning|research|tools|memory|interview)\b", content)
    route = match.group(1) if match else "finish"

    return {"next": route, "iterations": 1}
