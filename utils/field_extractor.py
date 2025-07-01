import re
from typing import Dict, Optional

def extract_fields_from_resume(text: str) -> Dict[str, Optional[str]]:
    """Extracts name, email, and phone number from resume text using regex and heuristics"""
    if not text or not text.strip():
        return {"name": "Candidate", "email": None, "phone": None}
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    email = email_match.group(0) if email_match else None
    
    phone_patterns = [
        r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
        r'\+?[0-9]{1,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}',
        r'\([0-9]{3}\)[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
    ]
    
    phone = None
    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            phone = re.sub(r'[^\d+]', '', phone_match.group(0))
            if len(phone) >= 10:
                phone = phone_match.group(0).strip()
                break

    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    name = None

    for line in lines[:5]:
        if any([
            len(line) > 50,
            '@' in line,
            re.search(r'\d{3,}', line),
            line.lower() in ['resume', 'cv', 'curriculum vitae'],
            len(line.split()) > 4,
            len(line) < 2,
        ]):
            continue
            
        if re.match(r'^[A-Za-z\s\.-]{2,30}$', line):
            words = line.split()
            if 1 <= len(words) <= 3 and all(word[0].isupper() for word in words):
                name = line
                break
    
    return {
        "name": name or "Candidate",
        "email": email,
        "phone": phone
    }