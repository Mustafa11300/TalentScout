"""
Technical Question Generator
=============================
Generates screening questions for each technology in the candidate's
declared stack.

This module provides a *fallback* question bank so the chatbot works
without an LLM key configured.  When an LLM is available (Phase 3+),
``generate_questions_via_llm()`` will call the model using the prompt
from ``prompts.py`` and return richer, contextual questions.
"""

from __future__ import annotations

# Static question bank (fallback / offline mode)

_QUESTION_BANK: dict[str, list[dict]] = {
    "python": [
        {"question": "What is the Global Interpreter Lock (GIL) and how does it affect multi-threaded Python programs?", "difficulty": "medium"},
        {"question": "Explain the difference between a list and a tuple. When would you choose one over the other?", "difficulty": "easy"},
        {"question": "Describe how Python's garbage collector works, including reference counting and the cyclic garbage collector.", "difficulty": "hard"},
    ],
    "javascript": [
        {"question": "What is the event loop in JavaScript and how does it handle asynchronous operations?", "difficulty": "medium"},
        {"question": "Explain the difference between `var`, `let`, and `const`.", "difficulty": "easy"},
        {"question": "How does prototypal inheritance work in JavaScript, and how does it differ from classical inheritance?", "difficulty": "hard"},
    ],
    "react": [
        {"question": "What are React hooks and why were they introduced?", "difficulty": "easy"},
        {"question": "Explain the virtual DOM and React's reconciliation algorithm.", "difficulty": "medium"},
        {"question": "Describe how you would optimize a React application that has performance issues due to excessive re-renders.", "difficulty": "hard"},
    ],
    "node.js": [
        {"question": "What is the role of the `package.json` file in a Node.js project?", "difficulty": "easy"},
        {"question": "Explain the difference between `require()` and `import` in Node.js.", "difficulty": "medium"},
        {"question": "How would you handle memory leaks in a long-running Node.js application?", "difficulty": "hard"},
    ],
    "django": [
        {"question": "What is Django's ORM and how does it map Python classes to database tables?", "difficulty": "easy"},
        {"question": "Explain the request/response lifecycle in Django.", "difficulty": "medium"},
        {"question": "How would you design a Django project to handle 10,000 concurrent WebSocket connections?", "difficulty": "hard"},
    ],
    "flask": [
        {"question": "What are Flask blueprints and when would you use them?", "difficulty": "easy"},
        {"question": "Compare Flask's request context and application context.", "difficulty": "medium"},
        {"question": "How would you implement rate limiting and authentication middleware in a Flask API?", "difficulty": "hard"},
    ],
    "sql": [
        {"question": "What is the difference between an INNER JOIN and a LEFT JOIN?", "difficulty": "easy"},
        {"question": "Explain database normalization and the first three normal forms.", "difficulty": "medium"},
        {"question": "How would you optimize a slow SQL query on a table with millions of rows?", "difficulty": "hard"},
    ],
    "postgresql": [
        {"question": "What are the advantages of PostgreSQL over MySQL?", "difficulty": "easy"},
        {"question": "Explain MVCC (Multi-Version Concurrency Control) in PostgreSQL.", "difficulty": "medium"},
        {"question": "How do you use PostgreSQL's EXPLAIN ANALYZE to diagnose and fix query performance?", "difficulty": "hard"},
    ],
    "docker": [
        {"question": "What is the difference between a Docker image and a Docker container?", "difficulty": "easy"},
        {"question": "Explain the concept of Docker layers and how they affect image size.", "difficulty": "medium"},
        {"question": "How would you design a multi-stage Docker build for a production Python application?", "difficulty": "hard"},
    ],
    "aws": [
        {"question": "What is the difference between EC2, ECS, and Lambda?", "difficulty": "easy"},
        {"question": "Explain the shared responsibility model in AWS.", "difficulty": "medium"},
        {"question": "Design a highly available, fault-tolerant architecture for a web application using AWS services.", "difficulty": "hard"},
    ],
    "java": [
        {"question": "What is the difference between `==` and `.equals()` in Java?", "difficulty": "easy"},
        {"question": "Explain the Java Memory Model and how `volatile` and `synchronized` work.", "difficulty": "medium"},
        {"question": "How does the JVM's garbage collection work, and what are the differences between G1, ZGC, and Shenandoah?", "difficulty": "hard"},
    ],
    "typescript": [
        {"question": "What are the benefits of using TypeScript over plain JavaScript?", "difficulty": "easy"},
        {"question": "Explain the difference between `interface` and `type` in TypeScript.", "difficulty": "medium"},
        {"question": "How would you use conditional types and mapped types to create a deeply partial version of a complex type?", "difficulty": "hard"},
    ],
    "go": [
        {"question": "What are goroutines and how do they differ from OS threads?", "difficulty": "easy"},
        {"question": "Explain how channels work in Go and when you would use buffered vs. unbuffered channels.", "difficulty": "medium"},
        {"question": "How does Go's garbage collector work, and what strategies would you use to minimize GC pause times?", "difficulty": "hard"},
    ],
    "kubernetes": [
        {"question": "What is a Pod in Kubernetes and how does it relate to containers?", "difficulty": "easy"},
        {"question": "Explain the difference between a Deployment, StatefulSet, and DaemonSet.", "difficulty": "medium"},
        {"question": "How would you design a zero-downtime deployment strategy using Kubernetes?", "difficulty": "hard"},
    ],
    "rust": [
        {"question": "What is Rust's ownership model and why is it significant?", "difficulty": "easy"},
        {"question": "Explain the borrow checker and the difference between mutable and immutable references.", "difficulty": "medium"},
        {"question": "How do lifetimes work in Rust, and when would you need to use explicit lifetime annotations?", "difficulty": "hard"},
    ],
}

# Generic questions for technologies not in the bank
_GENERIC_QUESTIONS: list[dict] = [
    {"question": "What are the core features of {tech} and why would you choose it over alternatives?", "difficulty": "easy"},
    {"question": "Describe a challenging project where you used {tech}. What problems did you encounter and how did you solve them?", "difficulty": "medium"},
    {"question": "How would you architect a production-grade system using {tech}, and what best practices would you follow?", "difficulty": "hard"},
]


# Public API

def build_question_queue(tech_stack: list[str], questions_per_tech: int = 3) -> list[dict]:
    """
    Build an ordered list of questions for the given tech stack.

    Each item is a dict with keys: technology, question, difficulty.

    Parameters
    ----------
    tech_stack : list[str]
        Technologies declared by the candidate.
    questions_per_tech : int
        Number of questions per technology (default 3).

    Returns
    -------
    list[dict]
        Flat, ordered question queue ready for the state machine to
        iterate through.
    """
    queue: list[dict] = []

    for tech in tech_stack:
        key = tech.lower().strip()
        bank = _QUESTION_BANK.get(key)

        if bank:
            questions = bank[:questions_per_tech]
        else:
            # Use generic questions with the technology name interpolated
            questions = [
                {
                    "question": q["question"].format(tech=tech),
                    "difficulty": q["difficulty"],
                }
                for q in _GENERIC_QUESTIONS[:questions_per_tech]
            ]

        for q in questions:
            queue.append({
                "technology": tech,
                "question": q["question"],
                "difficulty": q["difficulty"],
            })

    return queue
