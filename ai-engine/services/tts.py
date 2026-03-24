from io import BytesIO
from gtts import gTTS


def synthesize_speech(text: str, lang: str = "en") -> bytes:
    if not text or not text.strip():
        raise ValueError("Text is required for TTS")
    audio_fp = BytesIO()
    tts = gTTS(text=text, lang=lang)
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    return audio_fp.read()
