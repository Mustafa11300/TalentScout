# 🎯 TalentScout Hiring Assistant

An intelligent, LLM-powered hiring assistant chatbot built with Python and Streamlit. This application conducts initial candidate screening by securely collecting candidate information, dynamically generating technical interview questions based on the candidate's tech stack, and seamlessly maintaining conversation context using a state machine framework.

## 🌟 Features

- **Dynamic State Machine:** The conversation is strictly controlled via a 6-phase state machine (Greeting, Info Gathering, Tech Declaration, Tech Questioning, Wrap Up, Ended). This prevents the LLM from going "off-the-rails" while allowing for natural dialogue inside each state.
- **Robust Field Extraction:** A hybrid extraction strategy. We use zero-shot LLM prompts to extract structured JSON data from free-flowing text. If that fails (or API quota is hit), we fall back to a highly resilient Regex and Substring heuristic engine. Fixes were applied to prevent "greedy" parsing (e.g., matching "Mumbai" as a role title).
- **Dynamic Question Generation:** Utilizing an LLM model (Gemini/OpenAI) to generate customized technical questions spanning Easy, Medium, and Hard difficulties based on the specific tech stack the candidate declared. Fallbacks to a static question bank if offline.
- **Bonus & Enhancements:**
  - **Sentiment Analysis & Personalization:** The system prompt explicitly instructs the LLM to gauge the emotion of the candidate and adapt its tone (e.g., empathetic for nervous candidates). The LLM also utilizes captured variables to personalize responses.
  - **Multilingual Support:** As an LLM-driven bot, the assistant is instructed to automatically adapt to and reply in the user's chosen language.
  - **Premium UI & UX:** A highly customized injection of modern CSS variables. Featuring gradient headings, a "live" Candidate Profile sidebar card, and glassmorphic micro-adjustments that completely hide default Streamlit branding.
  - **Performance Optimization:** Implemented through lightweight UI updates and concurrent thread handling logic inherently present in the Streamlit runtime, alongside modular tool functions.

## 🛠️ Technology Stack

- **Backend Logic / Processing:** Python 3.9+
- **Frontend UI / Client:** Streamlit (Custom CSS)
- **AI Core:** OpenAI API / Google Gemini API (via HTTPX + OpenAI SDK wrapper)
- **Data Validation & Modeling:** Pydantic

## 📂 Repository Structure

```text
TalentScout/
├── .env.example             # Template for API keys
├── .env                     # Local environment keys
├── app.py                   # Main Streamlit application
├── requirements.txt         # Dependency manifest
├── utils/
│   └── security.py          # Hashing, PII masking algorithms
├── data/
│   ├── schema.py            # Pydantic data models
│   └── session_store.py     # JSON snapshot persistence
└── chatbot/
    ├── context.py           # Message history management
    ├── extractor.py         # Advanced Regex/Heuristic parsing logic
    ├── llm_client.py        # Centralized LLM API interaction (OpenAI/Gemini)
    ├── prompts.py           # Core System Instruction and Stage-specific Prompts
    ├── question_gen.py      # LLM fallback static question generation
    └── state_machine.py     # Deterministic routing logic
```

## 🚀 Setup & Installation

Follow these steps to deploy your local instance:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/TalentScout.git
   cd TalentScout
   ```

2. **Set up a Virtual Environment & Install Dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Environment Setup:**
   Copy the example environment file and insert your active API keys.
   ```bash
   cp .env.example .env
   # Edit .env and paste your GEMINI_API_KEY or OPENAI_API_KEY
   ```

4. **Launch the Application:**
   ```bash
   streamlit run app.py
   ```
   *The assistant will launch locally at `http://localhost:8501/`*

## 🎬 Video Walkthrough Demo

A video walkthrough demonstrating the chatbot's real-time capabilities and handling of short fallback extraction patterns can be found via the Loom output or included WebP in the project release.

---
*Developed for LeadOps & TalentScout Initiatives.*
