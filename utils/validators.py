import re

def validate_email(email: str) -> bool:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    # simple length/digit check
    digits = re.sub(r"\D", "", phone)
    return len(digits) >= 10
