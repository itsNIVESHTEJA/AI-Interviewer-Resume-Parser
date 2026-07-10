"""
Text-to-Speech: generates an mp3 (via gTTS, needs internet, very reliable
on servers/cloud where pyttsx3's system voices aren't available) for a
given text and returns the bytes so Streamlit can play it with st.audio.
"""
from io import BytesIO
from gtts import gTTS


def synthesize_speech(text: str) -> bytes:
    """Returns mp3 audio bytes for the given text."""
    if not text.strip():
        return b""
    buf = BytesIO()
    tts = gTTS(text=text, lang="en")
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()
