"""
chatbot package
===============
Core conversation logic for the TalentScout Hiring Assistant.

Modules:
    state_machine — Conversation flow controller (6-state FSM)
    prompts       — All system/user prompt templates
    extractor     — Parse candidate info from free-text responses
    question_gen  — Tech-stack question generation
    context       — Message history management
"""

from chatbot.state_machine import StateMachine, ConversationState

__all__ = ["StateMachine", "ConversationState"]
