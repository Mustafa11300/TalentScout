"""
Data Schema
============
Pydantic models for structured candidate data.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class TechQuestion(BaseModel):
    """A single technical screening question."""
    technology: str
    question: str
    difficulty: str = Field(pattern=r"^(easy|medium|hard)$")


class TechAnswer(BaseModel):
    """A candidate's answer to a technical question."""
    technology: str
    question: str
    difficulty: str
    answer: str


class CandidateSession(BaseModel):
    """
    In-memory representation of everything collected during a
    screening session.  Stored in ``st.session_state`` and serialised
    to JSON on session end.
    """
    # Personal info (6 required fields)
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    experience: Optional[str] = None
    position: Optional[str] = None

    # Tech screening
    tech_stack: List[str] = Field(default_factory=list)
    tech_questions: List[TechQuestion] = Field(default_factory=list)
    tech_answers: List[TechAnswer] = Field(default_factory=list)

    @property
    def info_fields_collected(self) -> int:
        """Count of non-None personal info fields."""
        fields = [self.name, self.email, self.phone,
                  self.location, self.experience, self.position]
        return sum(1 for f in fields if f is not None)

    @property
    def info_complete(self) -> bool:
        """True when all 6 personal info fields have been collected."""
        return self.info_fields_collected == 6
