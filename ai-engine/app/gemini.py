import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI

from app.llm_utils import is_rate_limit_error

load_dotenv()

MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
MISTRAL_FALLBACK_MODEL = os.getenv("MISTRAL_FALLBACK_MODEL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_primary_llm = ChatMistralAI(
    model=MISTRAL_MODEL,
    api_key=os.getenv("MISTRAL_API_KEY"),
    temperature=0.3,
)

_fallback_llms = []

if MISTRAL_FALLBACK_MODEL and MISTRAL_FALLBACK_MODEL != MISTRAL_MODEL:
    _fallback_llms.append(
        ChatMistralAI(
            model=MISTRAL_FALLBACK_MODEL,
            api_key=os.getenv("MISTRAL_API_KEY"),
            temperature=0.3,
        )
    )

try:
    from langchain_openai import ChatOpenAI
except Exception:
    ChatOpenAI = None

if ChatOpenAI and os.getenv("OPENAI_API_KEY"):
    _fallback_llms.append(
        ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.3,
        )
    )


class FallbackChatModel:
    def __init__(self, primary, fallbacks):
        self._primary = primary
        self._fallbacks = fallbacks

    def invoke(self, prompt, **kwargs):
        try:
            return self._primary.invoke(prompt, **kwargs)
        except Exception as exc:
            if not is_rate_limit_error(exc) or not self._fallbacks:
                raise
            last_exc = exc
            for fb in self._fallbacks:
                try:
                    return fb.invoke(prompt, **kwargs)
                except Exception as fb_exc:
                    last_exc = fb_exc
            raise last_exc

    def __getattr__(self, name):
        return getattr(self._primary, name)


llm = FallbackChatModel(_primary_llm, _fallback_llms)
