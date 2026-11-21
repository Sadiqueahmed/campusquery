"""
llm_client.py — Unified LLM interface supporting Groq, Gemini, and Ollama.

Each provider returns raw text. The caller is responsible for JSON parsing.
Temperature 0 is used for SQL generation (deterministic output).
"""

import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()


def _get_config() -> dict:
    """Return provider-specific configuration."""
    if LLM_PROVIDER == "groq":
        return {
            "api_key": os.getenv("GROQ_API_KEY", ""),
            "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "url": "https://api.groq.com/openai/v1/chat/completions",
        }
    elif LLM_PROVIDER == "gemini":
        api_key = os.getenv("GEMINI_API_KEY", "")
        model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        return {
            "api_key": api_key,
            "model": model,
            "url": f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        }
    elif LLM_PROVIDER == "ollama":
        return {
            "api_key": "",  # Ollama is local, no key needed
            "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
            "url": os.getenv("OLLAMA_URL", "http://localhost:11434") + "/api/chat",
        }
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")


def is_configured() -> bool:
    """Check if the LLM provider has the necessary credentials."""
    cfg = _get_config()
    if LLM_PROVIDER in ("groq", "gemini"):
        key = cfg["api_key"]
        return bool(key) and not key.startswith("your_")
    # Ollama doesn't need a key
    return True


def get_provider_name() -> str:
    return LLM_PROVIDER


async def chat(system_prompt: str, user_message: str, temperature: float = 0) -> str:
    """
    Send a chat message to the configured LLM and return the response text.
    Raises httpx.HTTPStatusError or ValueError on failure.
    """
    cfg = _get_config()

    if LLM_PROVIDER in ("groq",):
        return await _chat_openai_compatible(cfg, system_prompt, user_message, temperature)
    elif LLM_PROVIDER == "gemini":
        return await _chat_gemini(cfg, system_prompt, user_message, temperature)
    elif LLM_PROVIDER == "ollama":
        return await _chat_ollama(cfg, system_prompt, user_message, temperature)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")


async def _chat_openai_compatible(cfg: dict, system: str, user: str, temp: float) -> str:
    """Groq uses the OpenAI-compatible API."""
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temp,
        "response_format": {"type": "json_object"},  # Groq supports JSON mode
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(cfg["url"], headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _chat_gemini(cfg: dict, system: str, user: str, temp: float) -> str:
    """Google Gemini REST API."""
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": temp,
            "responseMimeType": "application/json",
        },
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(cfg["url"], json=payload)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


async def _chat_ollama(cfg: dict, system: str, user: str, temp: float) -> str:
    """Local Ollama API."""
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": temp},
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(cfg["url"], json=payload)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
