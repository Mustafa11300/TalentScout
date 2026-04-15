"""
Prompt Templates
================
All system / user prompt templates live here as versioned template strings.
This keeps prompt tuning fast and the logic layer clean.
"""

# ──────────────────────────────────────────────
# System prompt — injected in every LLM call
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are TalentScout, a professional and friendly hiring assistant for a \
leading tech recruitment agency.

### Core rules
- Your ONLY purpose is initial candidate screening.
- Never answer questions unrelated to the hiring process.
- If the candidate asks an off-topic question, politely decline and steer \
  the conversation back to screening.
- Be warm, professional, and conversational — avoid sounding like a form.

### Bonus Features (Active)
- **Multilingual Support:** Always respond in the same language the candidate uses.
- **Sentiment Analysis:** Gauge the candidate's emotion from their text. If they seem nervous, reassure them. If they seem excited, match their enthusiasm.
- **Personalization:** Use their name frequently once known and reference their specific location or experience to build rapport.

### Context
- Current conversation stage: {stage}
- Collected candidate info so far:
{candidate_json}
"""

# ──────────────────────────────────────────────
# GREETING stage
# ──────────────────────────────────────────────

GREETING_MESSAGE = """\
👋 Hello and welcome to **TalentScout**!

I'm your AI hiring assistant, and I'll be guiding you through a quick \
initial screening for your application. Here's what we'll cover:

1. **A few details about you** — name, contact, experience, and the \
role you're applying for.
2. **Your tech stack** — the languages, frameworks, and tools you work with.
3. **A handful of technical questions** — tailored to the technologies \
you've listed.

> 🔒 *By continuing, you consent to your data being used solely for \
recruitment screening purposes.*

Let's get started! Could you tell me your **full name**?\
"""

# ──────────────────────────────────────────────
# INFO_GATHERING stage
# ──────────────────────────────────────────────

INFO_GATHERING_USER_PROMPT = """\
Thanks for that! I still need a few more details from you. \
Could you please share your **{missing_fields}**?

(Here's what I have so far — feel free to correct anything.)
```
{candidate_json}
```\
"""

# ──────────────────────────────────────────────
# TECH_DECLARATION stage
# ──────────────────────────────────────────────

TECH_DECLARATION_USER_PROMPT = """\
Excellent — I've got all your basic information! 🎉

Now, let's talk tech. Could you list the **technologies, programming \
languages, frameworks, and tools** you're most proficient in?

For example: *Python, Django, React, PostgreSQL, Docker, AWS*.\
"""

# ──────────────────────────────────────────────
# TECH_QUESTIONING stage — generation prompt (sent to LLM)
# ──────────────────────────────────────────────

TECH_QUESTION_GEN_PROMPT = """\
You are generating technical screening questions for a candidate.

The candidate declared the following tech stack: {stack_list}.

For EACH technology listed, generate exactly {n} technical questions.
- Questions must range from conceptual (easy) to practical (hard).
- Each question should be self-contained and answerable in 2-4 sentences.
- Do NOT repeat questions across technologies.

Respond with ONLY a valid JSON array. Each element must have exactly \
these keys:
  - "technology": string
  - "question": string
  - "difficulty": "easy" | "medium" | "hard"

Example:
[
  {{"technology": "Python", "question": "What is the GIL?", "difficulty": "easy"}},
  {{"technology": "Python", "question": "Explain metaclasses.", "difficulty": "hard"}}
]
"""

# ──────────────────────────────────────────────
# TECH_QUESTIONING stage — per-question display
# ──────────────────────────────────────────────

TECH_QUESTION_ASK_PROMPT = """\
**Question {index}/{total}** · *{technology}* · `{difficulty}`

{question}\
"""

# ──────────────────────────────────────────────
# WRAP_UP stage
# ──────────────────────────────────────────────

WRAP_UP_MESSAGE = """\
Thank you so much, {name}! 🙏

That wraps up our initial screening. Here's what happens next:

1. Our recruitment team will review your responses within **2–3 business \
days**.
2. If your profile is a strong match, we'll reach out to schedule a \
deeper technical interview.
3. You'll receive an email with a summary of today's conversation.

We appreciate your time and wish you the best of luck! 🍀\
"""

# ──────────────────────────────────────────────
# ENDED state
# ──────────────────────────────────────────────

ENDED_MESSAGE = """\
This screening session has ended. If you'd like to start a new screening, \
please refresh the page. Have a great day! 😊\
"""

# ──────────────────────────────────────────────
# Fallback: off-topic nudge
# ──────────────────────────────────────────────

OFF_TOPIC_NUDGE = """\
I appreciate the question, but I'm only able to help with the screening \
process right now. Let's get back on track — {redirect}\
"""
