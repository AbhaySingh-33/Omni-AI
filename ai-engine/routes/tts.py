from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from services.tts import synthesize_speech

router = APIRouter()


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    lang: str = "en"


@router.post("/tts")
def tts(req: TTSRequest):
    try:
        audio = synthesize_speech(req.text, req.lang)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Text-to-speech failed")

    return Response(content=audio, media_type="audio/mpeg")
