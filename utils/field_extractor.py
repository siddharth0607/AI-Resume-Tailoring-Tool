import re
from typing import Dict, Optional

def extract_fields_from_resume(text: str) -> Dict[str, Optional[str]]:
    """Extracts name, email, and phone number from resume text using regex and heuristics"""
    if not text or not text.strip():
        return {"name": "Candidate", "email": None, "phone": None}

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    email = email_match.group(0) if email_match else None

    def extract_phone(text: str) -> Optional[str]:
        patterns = [
            r'(\+91[\s-]*[6-9]\d{2}[\s-]*\d{3}[\s-]*\d{4})',
            r'([6-9]\d{9})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                digits = re.sub(r'[^\d]', '', match.group())
                return '+91' + digits[-10:] if len(digits) >= 10 else None
        return None

    phone = extract_phone(text)

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
            if 1 <= len(words) <= 3 and all(w[0].isupper() for w in words if w.isalpha()):
                name = line
                break

    return {
        "name": name or "Candidate",
        "email": email,
        "phone": phone
    }