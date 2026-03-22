from fastapi import FastAPI
from pydantic import BaseModel
from graph.workflow import build_graph
from services.memory import save_chat

app = FastAPI()

graph = build_graph()


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def root():
    return {"message": "AI Engine Running 🚀"}


@app.post("/chat")
async def chat(req: ChatRequest):
    user_id = "default_user"

    result = graph.invoke({
        "messages": [("user", req.message)]
    })

    response = result["messages"][-1].content

    # ✅ SAVE MEMORY
    save_chat(user_id, req.message, response)

    return {
        "response": response
    }