"""
Candidate Info Extractor
========================
Parses free-text user messages to extract structured candidate fields.

Uses regex heuristics for email / phone / experience and simple keyword
detection for other fields.  A future enhancement could swap in an LLM
extraction sub-prompt for higher accuracy.
"""

import re
from typing import Optional
from data.schema import CandidateSession


# Common role / position keywords used to disambiguate
_ROLE_KEYWORDS = {
    "engineer", "developer", "architect", "manager", "lead",
    "analyst", "designer", "scientist", "admin", "devops",
    "sde", "swe", "frontend", "backend", "fullstack", "full stack",
    "intern", "consultant", "specialist", "coordinator", "tester",
    "qa", "data", "ml", "ai", "cloud", "security", "mobile",
    "programmer", "cto", "ceo", "vp", "director", "associate",
}


# Field extraction from free text

def extract_candidate_fields(text: str, current: CandidateSession) -> dict:
    """
    Attempt to extract candidate info fields from *text*.

    Returns a dict of ``{field_name: value}`` for every field that was
    confidently identified.  Fields already present in *current* are
    skipped so we don't overwrite confirmed data.

    Parameters
    ----------
    text : str
        The raw user message.
    current : CandidateSession
        The candidate session so far (used to know which fields are missing).

    Returns
    -------
    dict
        Extracted fields — only those that are non-empty.
    """
    extracted: dict = {}

    # Email
    if not current.email:
        email = _extract_email(text)
        if email:
            extracted["email"] = email

    # Phone
    if not current.phone:
        phone = _extract_phone(text)
        if phone:
            extracted["phone"] = phone

    # Experience (years)
    if not current.experience:
        exp = _extract_experience(text)
        if exp:
            extracted["experience"] = exp

    # Name
    if not current.name:
        name = _extract_name_explicit(text)
        if name:
            extracted["name"] = name

    # Location
    if not current.location:
        loc = _extract_location_explicit(text)
        if loc:
            extracted["location"] = loc

    # Position
    if not current.position:
        pos = _extract_position_explicit(text)
        if pos:
            extracted["position"] = pos

    # Short-answer fallback
    if not extracted:
        fallback = _extract_short_answer_fallback(text, current)
        if fallback:
            extracted.update(fallback)

    return extracted


# Tech stack parsing

def parse_tech_stack(text: str) -> list[str]:
    """
    Parse a comma / newline / bullet-separated list of technologies
    from the user's message.

    Returns a deduplicated list of technology names, title-cased.
    Empty list if nothing meaningful was found.
    """
    # Remove bullet markers and normalise separators
    cleaned = re.sub(r"[-•*]\s*", "", text)
    # Split on commas, newlines, semicolons, "and"
    parts = re.split(r"[,;\n]+|\band\b", cleaned)
    techs = []
    seen = set()
    for part in parts:
        t = part.strip().strip(".")
        if len(t) < 1 or len(t) > 40:
            continue
        key = t.lower()
        if key not in seen:
            seen.add(key)
            techs.append(t)
    return techs


# Private pattern-based helpers

def _extract_email(text: str) -> Optional[str]:
    match = re.search(r"[\w\.+\-]+@[\w\.\-]+\.\w+", text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> Optional[str]:
    match = re.search(r"[\+]?[\d\s\-\(\)]{7,15}", text)
    if match:
        digits = re.sub(r"\D", "", match.group(0))
        if len(digits) >= 7:
            return match.group(0).strip()
    return None


def _extract_experience(text: str) -> Optional[str]:
    """Look for patterns like '5 years', '3+ yrs', 'a decade', etc."""
    match = re.search(
        r"(\d{1,2}\+?\s*(?:years?|yrs?|yr))",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()

    # Fallback: "experience" keyword followed by a number
    match = re.search(
        r"experience[:\s]*(\d{1,2})\+?\s*(?:years?|yrs?)?",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip() + " years"

    return None


def _extract_name_explicit(text: str) -> Optional[str]:
    match = re.search(
        r"(?:my name is|i'?m|i am|name[:\s]*)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip().title()
    return None


def _extract_location_explicit(text: str) -> Optional[str]:
    match = re.search(
        r"(?:based in|from|located? (?:in|at)|location[:\s]*|live in|living in|city[:\s]*)\s+(.+?)(?:[,.]|$)",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip().title()
    return None


def _extract_position_explicit(text: str) -> Optional[str]:
    match = re.search(
        r"(?:applying for|role[:\s]*|position[:\s]*|interested in|want to be|looking for)\s+(.+?)(?:[,.]|$)",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip().title()
    return None


# Short-answer fallback

def _extract_short_answer_fallback(text: str, current: CandidateSession) -> Optional[dict]:
    """
    When the user gives a short standalone answer (e.g. 'Mumbai',
    'Software Engineer', 'John Doe'), figure out which missing field
    it most likely belongs to based on content heuristics.

    Returns a dict with one key-value if a match is found, else None.
    """
    stripped = text.strip()
    words = stripped.split()

    # Only applies to short answers (1-6 words, no structured data)
    if len(words) > 6 or len(words) < 1:
        return None

    # Skip if it contains email or phone (already handled by pattern matchers)
    if re.search(r"[@]", stripped) or re.search(r"\d{7,}", re.sub(r"\D", "", stripped)):
        return None

    lower = stripped.lower()

    # Check if it looks like a position/role (contains role keywords as whole words)
    is_role_like = any(re.search(r"\b" + re.escape(kw) + r"\b", lower) for kw in _ROLE_KEYWORDS)

    # Check if it looks like experience
    is_experience_like = bool(re.search(r"\d+\s*(?:years?|yrs?|yr)", lower, re.IGNORECASE))

    # Priority determination
    # We check the most specific signals first

    # Experience
    if not current.experience and is_experience_like:
        return {"experience": stripped}

    # Position (role keywords are a strong signal)
    if not current.position and is_role_like:
        return {"position": stripped.title()}

    # Fallback to free text fields
    if not current.name and not is_role_like:
        # If first word starts with a letter and it's 1-4 words, likely a name
        if len(words) <= 4 and words[0][0].isalpha():
            return {"name": stripped.title()}

    if not current.location:
        # Short text, no role keywords, no digits — likely a location
        if not re.search(r"\d", stripped) and words[0][0].isalpha():
            return {"location": stripped.title()}

    # Last resort
    if not current.position:
        return {"position": stripped.title()}

    return None
