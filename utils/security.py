import hashlib

def mask_email(email: str) -> str:
    if not email or '@' not in email:
        return email
    parts = email.split('@')
    name_part = parts[0]
    domain_part = parts[1]
    if len(name_part) <= 3:
        masked_name = name_part[0] + "***"
    else:
        masked_name = name_part[:3] + "***"
    return f"{masked_name}@{domain_part}"

def mask_phone(phone: str) -> str:
    if not phone or len(phone) < 4:
        return phone
    return phone[:3] + "***"

def hash_session_id(email: str, timestamp: str) -> str:
    data = f"{email}{timestamp}".encode('utf-8')
    return hashlib.sha256(data).hexdigest()
