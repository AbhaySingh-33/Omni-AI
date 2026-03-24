from datetime import datetime
from app.gemini import llm


def format_response(user_query: str, raw: str) -> str:
    today = datetime.now().strftime("%A, %B %d, %Y")
    prompt = f"""You are a helpful AI assistant. Today's date is {today}.
A user asked a question and you have the raw answer/data below.
Your job is to present it as a clean, well-structured, human-friendly response.

Rules:
- Be concise and direct
- Use bullet points or numbered lists where appropriate
- If it's weather/search data, summarize the key facts clearly
- If it's a calculation, show the result clearly
- If it's a file listing, format it neatly
- If it's code or terminal output, present it cleanly
- Never mention "tool", "MCP", "raw output", or internal system details
- Respond naturally as if you found this information yourself
- Always use today's date ({today}) when the user asks about the current date

User question: {user_query}

Raw data:
{raw}

Now write a clean, structured response:"""
    result = llm.invoke(prompt)
    return result.content
