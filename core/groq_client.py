"""
Thin wrapper around the Groq chat completion API.
All LLM calls in the app go through this module so the model name /
parameters are easy to change in one place.
"""
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_API_KEY = os.getenv("GROQ_API_KEY")
_client = Groq(api_key=_API_KEY) if _API_KEY else None

# Fast + capable model available on Groq. Change here if needed.
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def is_configured() -> bool:
    return _client is not None


def chat(messages, temperature: float = 0.6, max_tokens: int = 1024, json_mode: bool = False) -> str:
    """
    messages: list of {"role": "system"|"user"|"assistant", "content": str}
    Returns the assistant's text content.
    """
    if _client is None:
        raise RuntimeError(
            "GROQ_API_KEY not set. Add it to your .env file before running the app."
        )

    kwargs = dict(
        model=MODEL_NAME,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = _client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content


def chat_json(messages, temperature: float = 0.4, max_tokens: int = 1024) -> dict:
    """Call chat() forcing JSON output and parse it. Falls back to a best-effort
    extraction if the model wraps JSON in markdown fences."""
    raw = chat(messages, temperature=temperature, max_tokens=max_tokens, json_mode=True)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Last resort: find the first { ... } block
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            return json.loads(raw[start:end + 1])
        raise
