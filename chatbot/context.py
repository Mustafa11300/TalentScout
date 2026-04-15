"""
Context Manager
===============
Maintains the message history for the conversation.

The history is stored as a list of dicts compatible with the OpenAI
chat-completion message format::

    {"role": "system" | "user" | "assistant", "content": "..."}

This makes it trivial to pass directly to the LLM in later phases.
"""

from __future__ import annotations
from typing import Literal


MessageRole = Literal["system", "user", "assistant"]


class ContextManager:
    """
    Manages the ordered list of messages exchanged during a session.

    Attributes
    ----------
    messages : list[dict]
        Chat-completion-compatible message history.
    max_history : int
        Maximum number of user+assistant messages to retain (prevents
        token overflow when sending to the LLM).
    """

    def __init__(self, max_history: int = 50):
        self.messages: list[dict] = []
        self.max_history = max_history

    # ── add messages ───────────────────────────

    def add_system_message(self, content: str) -> None:
        """Set or replace the system message (always first)."""
        if self.messages and self.messages[0]["role"] == "system":
            self.messages[0]["content"] = content
        else:
            self.messages.insert(0, {"role": "system", "content": content})

    def add_user_message(self, content: str) -> None:
        """Append a user message and trim if over max_history."""
        self.messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant_message(self, content: str) -> None:
        """Append an assistant message and trim if over max_history."""
        self.messages.append({"role": "assistant", "content": content})
        self._trim()

    # ── read helpers ───────────────────────────

    def get_messages(self) -> list[dict]:
        """Return the full message list (for LLM calls)."""
        return list(self.messages)

    def get_display_messages(self) -> list[dict]:
        """Return only user + assistant messages (for the UI)."""
        return [m for m in self.messages if m["role"] != "system"]

    def get_last_user_message(self) -> str | None:
        """Return the content of the most recent user message."""
        for m in reversed(self.messages):
            if m["role"] == "user":
                return m["content"]
        return None

    def get_last_assistant_message(self) -> str | None:
        """Return the content of the most recent assistant message."""
        for m in reversed(self.messages):
            if m["role"] == "assistant":
                return m["content"]
        return None

    def clear(self) -> None:
        """Reset message history."""
        self.messages.clear()

    @property
    def length(self) -> int:
        """Number of messages (including system)."""
        return len(self.messages)

    # ── private ────────────────────────────────

    def _trim(self) -> None:
        """
        Keep the system message plus only the last ``max_history``
        user/assistant messages.
        """
        non_system = [m for m in self.messages if m["role"] != "system"]
        if len(non_system) > self.max_history:
            system = [m for m in self.messages if m["role"] == "system"]
            self.messages = system + non_system[-self.max_history:]
