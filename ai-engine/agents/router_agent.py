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

# Keywords that indicate emotional/mental health content → route to reasoning (with emotion prompt)
EMOTION_KEYWORDS = [
    "feeling sad", "feeling down", "depressed", "depression", "anxious", "anxiety",
    "stressed", "stress", "lonely", "alone", "scared", "afraid", "angry",
    "frustrated", "hopeless", "worthless", "give up", "can't cope", "overwhelmed",
    "burned out", "burnout", "crying", "panic", "self harm", "suicidal",
    "no hope", "end it all", "don't want to live", "hate myself", "hurt myself",
    "nobody cares", "feel empty", "numb", "broken", "miserable", "suffering",
    "mental health", "therapy", "counseling", "i'm not okay", "struggling",
    "can't take it", "falling apart", "losing it", "breaking down"
]

# Simple greetings and generic words that shouldn't require LLM routing
GREETING_KEYWORDS = [
    "hi", "hello", "hey", "good morning", "good evening", "how are you", 
    "what's up", "who are you", "help"
]

# Keywords that should route to memory agent directly.
MEMORY_KEYWORDS = [
    "remember", "earlier", "previous", "before", "last time", "history",
    "what did i say", "what did we talk", "from our conversation",
]

# Keywords that usually indicate tool action requests.
TOOLS_KEYWORDS = [
    "calculate", "calc", "search web", "google", "run command", "terminal",
    "list files", "read file", "write file", "create file", "weather", "news",
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
        # PRIORITY: Crisis detected by emotion engine → immediate reasoning with crisis prompt
        emotion_ctx = state.get("emotion_context")
        if emotion_ctx and emotion_ctx.get("is_crisis"):
            return {"next": "reasoning", "iterations": 1}

        # Fast-path: emotional/mental health content → reasoning (emotion prompts activate)
        if any(kw in last_content for kw in EMOTION_KEYWORDS):
            return {"next": "reasoning", "iterations": 1}

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

        # Fast-path: memory
        if any(kw in last_content for kw in MEMORY_KEYWORDS):
            return {"next": "memory", "iterations": 1}

        # Fast-path: tool requests
        if any(kw in last_content for kw in TOOLS_KEYWORDS):
            return {"next": "tools", "iterations": 1}

        # Default route avoids an extra LLM classification hop.
        return {"next": "reasoning", "iterations": 1}

    # --- SUPERVISOR LOGIC (Agent just spoke) ---
    # Retrieve the state to see which agent just answered
    agent_used = state.get("agent_used", "")

    # If the active agent is designed to provide direct answers, we don't need the LLM to tell us to finish.
    # This optimization cuts response times by skipping unnecessary supervisor LLM calls.
    if agent_used in ("reasoning", "research", "memory", "interview"):
        return {"next": "finish", "iterations": 1}

    # Tools agent already returns user-facing output (or explicit confirmation/cancel text).
    # Finishing here avoids an extra supervisor LLM roundtrip.
    if agent_used == "tools":
        return {"next": "finish", "iterations": 1}

    return {"next": "finish", "iterations": 1}
