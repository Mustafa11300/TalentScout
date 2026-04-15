import json
import os

SESSION_DIR = "sessions"

def save_session(session_data: dict, session_id: str):
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR)
    
    filepath = os.path.join(SESSION_DIR, f"{session_id}.json")
    with open(filepath, "w") as f:
        json.dump(session_data, f, indent=4)
