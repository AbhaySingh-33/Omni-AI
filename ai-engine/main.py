import nest_asyncio
nest_asyncio.apply()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth import router as auth_router
from routes.chat import router as chat_router
from routes.documents import router as documents_router
from routes.system import router as system_router
from routes.tts import router as tts_router
from routes.kg import router as kg_router
from routes.interview import router as interview_router
from routes.emotion import router as emotion_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(tts_router)
app.include_router(system_router)
app.include_router(kg_router)
app.include_router(interview_router)
app.include_router(emotion_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    try:
        from services.interview import init_interview_tables
        init_interview_tables()
        print("Interview prep tables initialized")
    except Exception as e:
        print(f"Warning: Could not initialize interview tables: {e}")

    try:
        from emotion.emotion_store import init_emotion_tables
        init_emotion_tables()
        print("Emotion tracking tables initialized")
    except Exception as e:
        print(f"Warning: Could not initialize emotion tables: {e}")

