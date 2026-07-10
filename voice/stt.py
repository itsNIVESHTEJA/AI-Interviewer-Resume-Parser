"""
Speech-to-Text: converts recorded audio bytes (wav) from the browser mic
into text using Google's free Web Speech API via the SpeechRecognition
library. Falls back gracefully with a clear error message on failure.
"""
from io import BytesIO
import speech_recognition as sr


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    audio_bytes: raw audio bytes (wav format) captured from the browser
    (e.g. via the audio_recorder_streamlit component).
    Returns the transcribed text, or "" on failure.
    """
    if not audio_bytes:
        return ""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(BytesIO(audio_bytes)) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        raise RuntimeError(f"Speech recognition service error: {e}")
    except Exception as e:
        raise RuntimeError(f"Could not process audio: {e}")
