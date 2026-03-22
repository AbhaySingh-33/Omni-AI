from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph.workflow import build_graph
from services.memory import save_chat
from app.gemini import llm
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()


class ChatRequest(BaseModel):
    message: str


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


@app.get("/")
def root():
    return {"status": "ok", "message": "OmniAI Engine is running"}


@app.post("/chat")
async def chat(req: ChatRequest):
    user_id = "default_user"

    result = graph.invoke({
        "messages": [("user", req.message)]
    })

    raw_response = result["messages"][-1].content
    final_response = format_response(req.message, raw_response)

    save_chat(user_id, req.message, final_response)

    return {
        "response": final_response
    }
