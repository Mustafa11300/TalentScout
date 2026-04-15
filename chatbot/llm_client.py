"""
LLM Client
===========
Wrapper around the OpenAI API (or compatible endpoint) for all LLM
calls in TalentScout.

Provides two modes:
    1. **Live mode** — calls the OpenAI API when OPENAI_API_KEY is set.
    2. **Offline mode** — returns the pre-built prompt text directly,
       so the chatbot still works without an API key (uses the static
       question bank and rule-based extraction).

All API calls are wrapped in try/except so failures never crash the
session.
"""

from __future__ import annotations

import json
import os
import logging
from typing import Optional

from dotenv import load_dotenv

# Use explicit path so .env is found regardless of CWD
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

logger = logging.getLogger(__name__)

# Configuration

# Support both Gemini and OpenAI keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("LLM_MODEL", "gemini-2.0-flash")
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

# Google's OpenAI-compatible endpoint for Gemini
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def _get_provider() -> tuple[str, str] | None:
    """Return (api_key, base_url) for the active LLM provider, or None."""
    if GEMINI_API_KEY:
        return GEMINI_API_KEY, GEMINI_BASE_URL
    if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
        return OPENAI_API_KEY, None  # default OpenAI base URL
    return None


def is_llm_available() -> bool:
    """Return True if any LLM API key is configured."""
    return _get_provider() is not None


# Chat completion

def chat_completion(
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> Optional[str]:
    """
    Send a list of messages to the LLM and return the assistant reply.

    Automatically routes to Gemini or OpenAI based on which key is set.

    Parameters
    ----------
    messages : list[dict]
        OpenAI-format messages (role + content).
    temperature : float
        Sampling temperature.
    max_tokens : int | None
        Max response tokens (defaults to LLM_MAX_TOKENS env var).

    Returns
    -------
    str | None
        The assistant's reply text, or None on failure.
    """
    provider = _get_provider()
    if not provider:
        return None

    api_key, base_url = provider

    try:
        import openai

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        client = openai.OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"LLM API call failed: {e}")
        return None


# Specialized LLM calls

def generate_conversational_reply(
    system_prompt: str,
    context_messages: list[dict],
    user_prompt: str,
) -> Optional[str]:
    """
    Generate a conversational assistant reply.

    Combines the system prompt, conversation history, and a user-side
    instruction prompt, then returns the LLM's response.
    """
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(context_messages)
    messages.append({"role": "user", "content": user_prompt})
    return chat_completion(messages, temperature=0.7)


def generate_tech_questions_via_llm(
    tech_stack: list[str],
    questions_per_tech: int = 3,
) -> Optional[list[dict]]:
    """
    Use the LLM to generate tech screening questions.

    Returns a parsed list of question dicts, or None on failure
    (in which case the caller should fall back to the static bank).
    """
    from chatbot.prompts import TECH_QUESTION_GEN_PROMPT

    prompt = TECH_QUESTION_GEN_PROMPT.format(
        stack_list=", ".join(tech_stack),
        n=questions_per_tech,
    )

    raw = chat_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=2048,
    )

    if not raw:
        return None

    try:
        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, IndexError):
        logger.warning("Failed to parse LLM question JSON, falling back to static bank")

    return None


def extract_fields_via_llm(
    user_text: str,
    missing_fields: list[str],
    system_prompt: str,
) -> Optional[dict]:
    """
    Use the LLM to extract structured candidate fields from free text.

    Returns a dict of extracted fields, or None on failure (caller
    falls back to regex-based extraction).
    """
    extraction_prompt = f"""
Extract the following fields from the candidate's message if present: {', '.join(missing_fields)}.

Candidate's message: "{user_text}"

Respond with ONLY a valid JSON object where keys are field names and values are
the extracted data. Only include fields you are confident about. Example:
{{"name": "John Doe", "email": "john@example.com"}}

If you cannot extract any field, respond with: {{}}
"""

    raw = chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": extraction_prompt},
        ],
        temperature=0.1,
        max_tokens=256,
    )

    if not raw:
        return None

    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, IndexError):
        logger.warning("Failed to parse LLM extraction JSON, falling back to regex")

    return None
