import pdfplumber
from collections import defaultdict
import re
import logging
from typing import Dict, List
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_analyzer():
    """Initialize a simple PDF parser"""
    try:
        import pdfplumber
        logger.info("PDF parser initialized successfully")
        return {"parser": "pdfplumber"}
    except ImportError as e:
        logger.error(f"Required libraries not installed: {e}")
        raise

def fix_spacing(text: str) -> str:
    """Adds missing spaces between glued words based on heuristics"""
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r'\bcontent\s*based\b', 'content-based', text, flags=re.IGNORECASE)
    text = re.sub(r'\breal\s*time\b', 'real-time', text, flags=re.IGNORECASE)
    text = re.sub(r'\bproduction\s*grade\b', 'production-grade', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def is_section_heading(line: str, all_lines: List[str], index: int) -> bool:
    line = line.strip()
    line_lower = line.lower()

    if len(line) > 80 or len(line) < 3:
        return False

    if ':' in line and len(line.split()) < 5:
        key_part = line.split(':')[0]
        if key_part.lower() not in ['summary', 'objective']:
            return False

    content_indicators = ['@', 'http', 'www', '.com', '.org', 'linkedin', 'github']
    if any(ind in line_lower for ind in content_indicators):
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
    if any(re.fullmatch(rf"\b{re.escape(keyword)}\b", line_lower) for keyword in section_keywords):
        return True

    if line.isupper() and 4 <= len(line) <= 50:
        return True
    words = line.split()
    if len(words) <= 4 and all(word.istitle() or word.isupper() for word in words):
        return True
    if line.endswith(':') and not line_lower.startswith('cgpa'):
        return True
    if re.fullmatch(r"[A-Za-z]{3,10}[0-9]{2,4}", line):
        return False

    if re.match(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", line, re.IGNORECASE):
        return False

    if sum(c.isalpha() for c in line) < len(line) * 0.5:
        return False

    return False

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""

    text = re.sub(r'\s+', ' ', text)

    text = re.sub(r'[^\w\s\-.,()/@#&+:;\'\"!?]', ' ', text)

    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def normalize_heading(text: str) -> str:
    """Normalize heading text to consistent keys"""
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

        'skills': 'Skills',
        'technical skills': 'Skills',
        'technologies' : 'Skills',
        'core competencies': 'Skills',
        'competencies': 'Skills',
        'expertise': 'Skills',
        'technical expertise': 'Skills',
        'key skills': 'Skills',

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
        'positions of responsibility': 'Achievements',

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

    return original_text.title()

def get_section_summary(sections: Dict[str, str]) -> Dict[str, int]:
    """Get a summary of sections and their word counts"""
    summary = {}
    for section, content in sections.items():
        word_count = len(content.split()) if content else 0
        summary[section] = word_count
    return summary

def parse_resume_sections(pdf_path: str, analyzer) -> Dict[str, str]:
    """Parse and extract structured resume sections from PDF"""
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
        
        for i, line in enumerate(all_lines):
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

    
    logger.info(f"Successfully parsed {len(result_sections)} sections")
    return result_sections

def debug_parse_resume(pdf_path: str, analyzer) -> Dict[str, str]:
    """Print debug info while parsing resume from PDF"""
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return {}
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Processing {len(pdf.pages)} pages")
        
        all_lines = []
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        all_lines.append(line)
        
        print(f"\nExtracted {len(all_lines)} lines:")
        for i, line in enumerate(all_lines[:20]):
            is_heading = is_section_heading(line, all_lines, i)
            print(f"{i:2d}: {'[H]' if is_heading else '   '} {line[:80]}")
        
        if len(all_lines) > 20:
            print(f"... and {len(all_lines) - 20} more lines")
    
    return parse_resume_sections(pdf_path, analyzer)