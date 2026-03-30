from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import base64

from app.auth import get_current_user
from app.guardrails.input_guard import validate_input
from app.guardrails.output_guard import validate_output
from core.app_state import graph
from services.formatting import format_response
from services.memory import save_chat
from services.tts import synthesize_speech
from services.kg import ingest_user_message

router = APIRouter()


def _save_chat_safe(user_id: str, checked_input: str, safe_response: str) -> None:
    try:
        save_chat(user_id, checked_input, safe_response)
    except Exception as exc:
        print(f"save_chat skipped: {exc}")


def _ingest_user_message_safe(checked_input: str, user_id: str) -> None:
    try:
        ingest_user_message(checked_input, user_id)
    except Exception as exc:
        print(f"KG message ingest skipped: {exc}")


class ChatRequest(BaseModel):
    message: str
    voice: bool = False
    voice_lang: Optional[str] = None


@router.post("/chat")
async def chat(req: ChatRequest, background_tasks: BackgroundTasks, user=Depends(get_current_user)):
    user_id = user["user_id"]

    is_valid, checked_input = validate_input(req.message)
    if not is_valid:
        return {"response": checked_input}

    result = graph.invoke({
        "messages": [("user", checked_input)],
        "user_id": user_id,
        "iterations": 0
    })
    raw_response = result["messages"][-1].content
    final_response = format_response(req.message, raw_response)
    safe_response = validate_output(final_response)

    agent_used = result.get("agent_used") or result.get("next", "reasoning")
    # Persist to DB/KG asynchronously after the response is sent.
    background_tasks.add_task(_save_chat_safe, user_id, checked_input, safe_response)
    background_tasks.add_task(_ingest_user_message_safe, checked_input, user_id)

    payload = {"response": safe_response, "agent": agent_used}

    if req.voice:
        try:
            audio_bytes = synthesize_speech(safe_response, req.voice_lang or "en")
            payload["audio_b64"] = base64.b64encode(audio_bytes).decode("ascii")
            payload["audio_mime"] = "audio/mpeg"
        except Exception as exc:
            payload["audio_error"] = f"TTS failed: {exc}"

    return payload


@router.get("/history")
def get_history(user=Depends(get_current_user)):
    from services.memory import get_history as fetch_history
    rows = fetch_history(user["user_id"], limit=50)
    messages = []
    for msg, resp in rows:
        messages.append({"role": "user", "content": msg})
        messages.append({"role": "assistant", "content": resp})
    return {"messages": messages}
