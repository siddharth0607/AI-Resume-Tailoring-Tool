import pdfplumber
from collections import defaultdict
import re
import logging
from typing import Dict, List
import os
from utils.field_extractor import extract_fields_from_resume
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_analyzer():
    """Checks and loads the PDF parser"""
    try:
        import pdfplumber
        logger.info("PDF parser initialized successfully")
        return {"parser": "pdfplumber"}
    except ImportError as e:
        logger.error(f"Required libraries not installed: {e}")
        raise

def clean_text(text: str) -> str:
    """Cleans text and removes unwanted characters"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\-.,()/@#&+:;\'\"!?]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def fix_spacing(text: str) -> str:
    """Adds missing spaces between words and digits"""
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r'\bcontent\s*based\b', 'content-based', text, flags=re.IGNORECASE)
    text = re.sub(r'\breal\s*time\b', 'real-time', text, flags=re.IGNORECASE)
    text = re.sub(r'\bproduction\s*grade\b', 'production-grade', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_section_heading(line: str, all_lines: List[str], index: int) -> bool:
    """Checks if a line is a section heading"""
    line = line.strip()
    line_lower = line.lower()
    words = line.split()

    if len(line) > 80 or len(line) < 3:
        return False

    if (len(words) >= 2 and len(words) <= 3 and 
        all(word.istitle() and word.isalpha() for word in words) and 
        len(line) < 50 and index < 5):
        return False

    if ':' in line and len(line.split()) < 5:
        key_part = line.split(':')[0]
        if key_part.lower() not in ['summary', 'objective']:
            return False

    content_indicators = ['@', 'http', 'www', '.com', '.org', 'linkedin', 'github', 
                         'phone', 'tel', 'email', 'gmail', 'yahoo', 'outlook']
    if any(ind in line_lower for ind in content_indicators):
        return False

    if re.match(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", line, re.IGNORECASE):
        return False

    if re.fullmatch(r"[A-Za-z]{3,10}[0-9]{2,4}", line):
        return False

    if sum(c.isalpha() for c in line) < len(line) * 0.5:
        return False

    if re.search(r'[\+]?[\d\s\-\(\)]{10,}', line):
        return False

    section_keywords = [
        'education', 'experience', 'skills', 'projects', 'certifications',
        'achievements', 'summary', 'objective', 'profile', 'contact',
        'languages', 'publications', 'volunteer', 'activities', 'interests',
        'references', 'awards', 'honors', 'training', 'courses',
        'technical skills', 'professional experience', 'work experience',
        'core competencies', 'career objective', 'professional summary',
        'personal details', 'contact information', 'positions of responsibility'
    ]

    if any(keyword == line_lower for keyword in section_keywords):
        return True

    if any(keyword in line_lower and len(line_lower.split()) <= 3 for keyword in section_keywords):
        return True

    if line.isupper() and 4 <= len(line) <= 50:
        return True

    if line.endswith(':') and not line_lower.startswith('cgpa'):
        return True
    
    return False

def normalize_heading(text: str) -> str:
    """Maps headings to standard section names"""
    if not text:
        return "Other"
    original_text = text.strip()
    text = text.strip().lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    mapping = {
        'education': 'Education',
        'educational background': 'Education',
        'academic background': 'Education',
        'academics': 'Education',
        'qualification': 'Education',
        'qualifications': 'Education',
        'educational background': 'Education',
        'education background' : 'Education',
        'experience': 'Experience',
        'work experience': 'Experience',
        'professional experience': 'Experience',
        'employment': 'Experience',
        'employment history': 'Experience',
        'work history': 'Experience',
        'career': 'Experience',
        'career history': 'Experience',
        'internship': 'Experience',
        'internships': 'Experience',
        'relevant experience': 'Experience',
        'skills': 'Skills',
        'technical skills': 'Skills',
        'technologies': 'Skills',
        'core competencies': 'Skills',
        'competencies': 'Skills',
        'expertise': 'Skills',
        'technical expertise': 'Skills',
        'key skills': 'Skills',
        'proficiencies': 'Skills',
        'projects': 'Projects',
        'project': 'Projects',
        'portfolio': 'Projects',
        'key projects': 'Projects',
        'certifications': 'Certifications',
        'certification': 'Certifications',
        'certificates': 'Certifications',
        'licenses': 'Certifications',
        'professional certifications': 'Certifications',
        'achievements': 'Achievements',
        'accomplishments': 'Achievements',
        'awards': 'Achievements',
        'honors': 'Achievements',
        'summary': 'Summary',
        'professional summary': 'Summary',
        'profile': 'Summary',
        'professional profile': 'Summary',
        'objective': 'Summary',
        'career objective': 'Summary',
        'about': 'Summary',
        'about me': 'Summary',
        'contact': 'Contact',
        'contact information': 'Contact',
        'personal details': 'Contact',
        'personal information': 'Contact',
        'languages': 'Languages',
        'publications': 'Publications',
        'research': 'Publications',
        'positions of responsibility': 'Volunteer',
        'volunteer': 'Volunteer',
        'volunteer experience': 'Volunteer',
        'activities': 'Activities',
        'interests': 'Interests',
        'hobbies': 'Interests',
        'references': 'References',
        'training': 'Training',
        'courses': 'Training',
    }

    for key, value in mapping.items():
        if re.search(r'\b' + re.escape(key) + r'\b', text):
            return value
    if any(kw in original_text.lower() for kw in ['email', 'phone', 'linkedin', 'github']):
        return "Contact"
    
    words = original_text.split()
    if len(words) == 2 and all(word.istitle() and word.isalpha() for word in words):
        return "Contact Information"

    return original_text.title()

def get_section_summary(sections: Dict[str, str]) -> Dict[str, int]:
    """Returns word count per section"""
    summary = {}
    for section, content in sections.items():
        word_count = len(content.split()) if content else 0
        summary[section] = word_count
    return summary

def parse_resume_sections(pdf_path: str, analyzer) -> Dict[str, str]:
    """Parses a resume PDF into structured sections"""
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return {}

    sections = defaultdict(list)
    current_section = "Header"

    with pdfplumber.open(pdf_path) as pdf:
        logger.info(f"Processing {len(pdf.pages)} pages")

        all_lines = []
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    all_lines.append(line)

        logger.info(f"Extracted {len(all_lines)} lines total")

        skip_indices = set()
        for idx, line in enumerate(all_lines[:5]):
            stripped = line.strip()

            if re.fullmatch(r"[A-Z][a-z]+(\s+[A-Z][a-z]+)+", stripped):
                skip_indices.add(idx)
                continue

            if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', stripped):
                skip_indices.add(idx)
                continue

            if re.search(r'[\+]?[\d\s\-()]{10,}', stripped):
                skip_indices.add(idx)
                continue

            if re.search(r'(https?://|www\.|[a-zA-Z0-9]+\.(com|org|net|io|in|ai))', stripped):
                skip_indices.add(idx)
                continue

        for i, line in enumerate(all_lines):
            if i in skip_indices:
                continue

            cleaned_line = fix_spacing(clean_text(line))
            if len(cleaned_line) < 2:
                continue

            if is_section_heading(line, all_lines, i):
                section_name = normalize_heading(line)
                current_section = section_name
                logger.debug(f"Found section: {current_section}")
                continue

            sections[current_section].append(cleaned_line)

    result_sections = {}
    for section, lines in sections.items():
        if lines:
            content = ' '.join(lines)
            if len(content.strip()) > 5:
                result_sections[section] = content.strip()

    full_text = '\n'.join(all_lines)
    contact_info = extract_fields_from_resume(full_text)

    header_info = []
    if contact_info.get("name"):
        header_info.append(f"Name: {contact_info['name']}")
    if contact_info.get("email"):
        header_info.append(f"Email: {contact_info['email']}")
    if contact_info.get("phone"):
        header_info.append(f"Phone: {contact_info['phone']}")

    link_pattern = r'(https?://[^\s)]+|www\.[^\s)]+|[a-zA-Z0-9]+\.(com|org|net|in|ai|io)/[^\s)]*)'
    top_text = ' '.join(all_lines[:10])
    links = re.findall(link_pattern, top_text, flags=re.IGNORECASE)
    for match in links:
        full_link = match[0]
        if full_link not in header_info:
            header_info.append(f"Link: {full_link}")

    if "Header" in result_sections and header_info:
        combined_header = result_sections["Header"] + "\n" + '\n'.join(header_info)
        result_sections["Contact Information"] = combined_header
        del result_sections["Header"]
    elif header_info:
        result_sections["Contact Information"] = '\n'.join(header_info)
    elif "Header" in result_sections:
        result_sections["Contact Information"] = result_sections["Header"]
        del result_sections["Header"]

    logger.info(f"Successfully parsed {len(result_sections)} sections")
    return result_sections