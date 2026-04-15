"""
Conversation State Machine
==========================
Controls the chatbot's progression through 6 discrete states:
    GREETING → INFO_GATHERING → TECH_DECLARATION → TECH_QUESTIONING → WRAP_UP → ENDED

Exit keywords (bye, quit, exit, stop, end) are detected on every user
message *before* any state-specific logic runs, jumping the machine
straight to WRAP_UP.

When an OpenAI API key is configured the machine uses the LLM for
conversational replies and field extraction; otherwise it falls back to
regex-based extraction and static prompt text.
"""

from enum import Enum, auto
from typing import Optional

from chatbot.context import ContextManager
from chatbot.extractor import extract_candidate_fields, parse_tech_stack
from chatbot.question_gen import build_question_queue
from chatbot.llm_client import (
    is_llm_available,
    generate_conversational_reply,
    generate_tech_questions_via_llm,
    extract_fields_via_llm,
)
from chatbot.prompts import (
    SYSTEM_PROMPT,
    GREETING_MESSAGE,
    INFO_GATHERING_USER_PROMPT,
    TECH_DECLARATION_USER_PROMPT,
    TECH_QUESTION_GEN_PROMPT,
    TECH_QUESTION_ASK_PROMPT,
    WRAP_UP_MESSAGE,
    ENDED_MESSAGE,
    OFF_TOPIC_NUDGE,
)
from data.schema import CandidateSession


# ──────────────────────────────────────────────
# State enum
# ──────────────────────────────────────────────

class ConversationState(Enum):
    """The six discrete stages of a screening conversation."""
    GREETING = auto()
    INFO_GATHERING = auto()
    TECH_DECLARATION = auto()
    TECH_QUESTIONING = auto()
    WRAP_UP = auto()
    ENDED = auto()


# Keywords that trigger an immediate jump to WRAP_UP
EXIT_KEYWORDS = {"bye", "quit", "exit", "stop", "end", "goodbye", "done"}

# The 6 info-gathering fields we need before moving on
REQUIRED_INFO_FIELDS = ["name", "email", "phone", "location", "experience", "position"]


# ──────────────────────────────────────────────
# State Machine
# ──────────────────────────────────────────────

class StateMachine:
    """
    Manages conversation state, transition logic, and orchestrates
    calls to the LLM via prompts/context.  All mutable session data
    lives here so it can be serialised into ``st.session_state``.
    """

    def __init__(self):
        self.state: ConversationState = ConversationState.GREETING
        self.candidate = CandidateSession()
        self.context = ContextManager()
        self.question_queue: list[dict] = []       # generated tech questions
        self.current_question_index: int = 0       # pointer into queue
        self.tech_answers: list[dict] = []          # candidate answers
        self._greeting_sent: bool = False

    # ── public API ──────────────────────────────

    def get_greeting(self) -> str:
        """Return the initial greeting message (called once on session start)."""
        greeting = GREETING_MESSAGE
        self.context.add_assistant_message(greeting)
        self._greeting_sent = True
        return greeting

    def handle_user_message(self, user_text: str) -> str:
        """
        Main entry point: accept a user message, run exit detection,
        delegate to the current state handler, and return the assistant
        reply.
        """
        self.context.add_user_message(user_text)

        # ── Exit keyword detection (runs before state logic) ──
        if self._is_exit_request(user_text) and self.state not in (
            ConversationState.WRAP_UP,
            ConversationState.ENDED,
        ):
            self.state = ConversationState.WRAP_UP

        # ── State dispatch ──
        handler = {
            ConversationState.GREETING: self._handle_greeting,
            ConversationState.INFO_GATHERING: self._handle_info_gathering,
            ConversationState.TECH_DECLARATION: self._handle_tech_declaration,
            ConversationState.TECH_QUESTIONING: self._handle_tech_questioning,
            ConversationState.WRAP_UP: self._handle_wrap_up,
            ConversationState.ENDED: self._handle_ended,
        }[self.state]

        reply = handler(user_text)
        self.context.add_assistant_message(reply)
        return reply

    def build_system_prompt(self) -> str:
        """Render the system prompt with live session data injected."""
        return SYSTEM_PROMPT.format(
            stage=self.state.name,
            candidate_json=self.candidate.model_dump_json(indent=2),
        )

    def get_missing_info_fields(self) -> list[str]:
        """Return a list of info fields that have not yet been collected."""
        data = self.candidate.model_dump()
        return [f for f in REQUIRED_INFO_FIELDS if not data.get(f)]

    def get_progress(self) -> tuple[int, int]:
        """Return (collected, total) for the info-gathering progress bar."""
        total = len(REQUIRED_INFO_FIELDS)
        collected = total - len(self.get_missing_info_fields())
        return collected, total

    # ── state handlers (private) ────────────────

    def _handle_greeting(self, user_text: str) -> str:
        """
        GREETING → INFO_GATHERING
        Transition trigger: user sends *any* message.
        """
        self.state = ConversationState.INFO_GATHERING
        # Immediately try to extract info from the first message
        return self._handle_info_gathering(user_text)

    def _handle_info_gathering(self, user_text: str) -> str:
        """
        Collect name, email, phone, location, experience, and position.
        Transition trigger: all 6 fields extracted.
        """
        # ── Try LLM-based extraction first, fall back to regex ──
        missing = self.get_missing_info_fields()

        if is_llm_available():
            llm_extracted = extract_fields_via_llm(
                user_text, missing, self.build_system_prompt()
            )
            if llm_extracted:
                self._merge_extracted(llm_extracted)

        # Always run regex extraction as a safety net
        regex_extracted = extract_candidate_fields(user_text, self.candidate)
        self._merge_extracted(regex_extracted)

        missing = self.get_missing_info_fields()

        if not missing:
            # All info collected → move to tech declaration
            self.state = ConversationState.TECH_DECLARATION
            reply = TECH_DECLARATION_USER_PROMPT
            # Try to make it conversational via LLM
            if is_llm_available():
                llm_reply = generate_conversational_reply(
                    self.build_system_prompt(),
                    self.context.get_display_messages()[-6:],
                    "All 6 candidate info fields have been collected. "
                    "Acknowledge what we know, then ask the candidate to list "
                    "their tech stack (languages, frameworks, tools).",
                )
                if llm_reply:
                    reply = llm_reply
            return reply
        else:
            # Still missing fields — ask for them
            fields_to_ask = missing[:2]
            fallback = INFO_GATHERING_USER_PROMPT.format(
                missing_fields=", ".join(fields_to_ask),
                candidate_json=self.candidate.model_dump_json(indent=2),
            )

            if is_llm_available():
                llm_reply = generate_conversational_reply(
                    self.build_system_prompt(),
                    self.context.get_display_messages()[-6:],
                    f"We still need these fields: {', '.join(fields_to_ask)}. "
                    f"Ask for them conversationally (1-2 at a time). "
                    f"Do NOT dump all missing fields at once.",
                )
                if llm_reply:
                    return llm_reply

            return fallback

    def _handle_tech_declaration(self, user_text: str) -> str:
        """
        TECH_DECLARATION → TECH_QUESTIONING
        Transition trigger: tech stack list parsed from user message.
        """
        techs = parse_tech_stack(user_text)

        if not techs:
            return (
                "I didn't quite catch your tech stack. Could you list the "
                "technologies, languages, and frameworks you work with? "
                "For example: *Python, React, PostgreSQL, Docker*."
            )

        self.candidate.tech_stack = techs

        # ── Two-pass question generation ──
        # Pass 1: try LLM, fall back to static bank
        if is_llm_available():
            llm_questions = generate_tech_questions_via_llm(techs)
            if llm_questions:
                self.question_queue = llm_questions
            else:
                self.question_queue = build_question_queue(techs)
        else:
            self.question_queue = build_question_queue(techs)

        self.current_question_index = 0
        self.state = ConversationState.TECH_QUESTIONING

        # Pass 2: ask them one-by-one
        return self._ask_next_question(preamble=True)

    def _handle_tech_questioning(self, user_text: str) -> str:
        """
        TECH_QUESTIONING → WRAP_UP
        Transition trigger: all questions asked (and answered).
        """
        # Record the answer to the *previous* question
        if self.current_question_index > 0:
            prev_q = self.question_queue[self.current_question_index - 1]
            self.tech_answers.append({
                "technology": prev_q["technology"],
                "question": prev_q["question"],
                "difficulty": prev_q["difficulty"],
                "answer": user_text,
            })

        if self.current_question_index >= len(self.question_queue):
            # All questions answered → wrap up
            self.state = ConversationState.WRAP_UP
            return self._handle_wrap_up(user_text)

        return self._ask_next_question()

    def _handle_wrap_up(self, _user_text: str) -> str:
        """
        Thank the candidate and describe next steps.
        Transition: immediately move to ENDED.
        """
        self.state = ConversationState.ENDED
        return WRAP_UP_MESSAGE.format(name=self.candidate.name or "there")

    def _handle_ended(self, _user_text: str) -> str:
        """Terminal state — reject further substantive input."""
        return ENDED_MESSAGE

    # ── helpers ─────────────────────────────────

    def _is_exit_request(self, text: str) -> bool:
        """Check if the user message contains an exit keyword."""
        words = set(text.lower().split())
        return bool(words & EXIT_KEYWORDS)

    def _merge_extracted(self, extracted: dict) -> None:
        """Merge extracted fields into the candidate model (never overwrite)."""
        for key, value in extracted.items():
            if value and hasattr(self.candidate, key):
                current_val = getattr(self.candidate, key)
                if not current_val:  # only set if currently empty
                    setattr(self.candidate, key, value)

    def _ask_next_question(self, preamble: bool = False) -> str:
        """Pop the next question from the queue and format it for the user."""
        if self.current_question_index >= len(self.question_queue):
            self.state = ConversationState.WRAP_UP
            return WRAP_UP_MESSAGE.format(name=self.candidate.name or "there")

        q = self.question_queue[self.current_question_index]
        self.current_question_index += 1

        idx = self.current_question_index
        total = len(self.question_queue)

        question_text = TECH_QUESTION_ASK_PROMPT.format(
            index=idx,
            total=total,
            technology=q["technology"],
            difficulty=q["difficulty"],
            question=q["question"],
        )

        if preamble:
            header = (
                f"Great! I've prepared **{total} technical question(s)** based on "
                f"your stack: **{', '.join(self.candidate.tech_stack)}**.\n\n"
                "Let's go through them one at a time.\n\n"
            )
            return header + question_text

        return question_text
