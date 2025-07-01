from openai import OpenAI
import os
import re
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BANNED_WORDS = [
    'spearheaded', 'leveraged', 'orchestrated', 'synergized', 'pioneered', 
    'revolutionized', 'passionate', 'dedicated', 'results-driven', 'dynamic',
    'innovative', 'cutting-edge', 'state-of-the-art', 'exceptional'
]

def clean_buzzwords(text: str) -> str:
    """Replace buzzwords with natural alternatives."""
    replacements = {
        'spearheaded': 'led', 'leveraged': 'used', 'orchestrated': 'managed',
        'synergized': 'collaborated', 'pioneered': 'started', 'revolutionized': 'improved',
        'passionate': '', 'dedicated': '', 'results-driven': '', 'dynamic': '',
        'innovative': 'new', 'cutting-edge': 'advanced', 'state-of-the-art': 'modern',
        'exceptional': 'strong'
    }
    
    for buzzword, replacement in replacements.items():
        pattern = r'\b' + re.escape(buzzword) + r'\b'
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_candidate_keywords(resume_text: str) -> set:
    """Extract actual skills, tools, and technologies mentioned in resume."""
    skill_patterns = [
        r'\b[A-Z]{2,}\b',
        r'\b(?:Python|JavaScript|Java|React|Node|Angular|Vue|Docker|Git|Excel|Tableau|Salesforce|SAP|AutoCAD|Photoshop)\b',
        r'\b(?:project management|data analysis|customer service|team leadership|budget management)\b',
        r'\b\w+(?:Script|SQL|JS|DB)\b', 
    ]
    
    found_skills = set()
    for pattern in skill_patterns:
        matches = re.findall(pattern, resume_text, re.IGNORECASE)
        found_skills.update([match.lower() for match in matches])
    
    return found_skills

def validate_against_resume(original_resume: str, rewritten_text: str) -> str:
    """Ensure rewritten text doesn't add information not in original resume."""
    original_keywords = extract_candidate_keywords(original_resume)
    
    original_years = set(re.findall(r'\b(\d+)\s*(?:years?|yrs?)\b', original_resume.lower()))
    rewritten_years = set(re.findall(r'\b(\d+)\s*(?:years?|yrs?)\b', rewritten_text.lower()))
    
    if rewritten_years - original_years:
        for year in rewritten_years - original_years:
            pattern = rf'\b{year}\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)\b'
            rewritten_text = re.sub(pattern, '', rewritten_text, flags=re.IGNORECASE)
    
    return clean_buzzwords(rewritten_text)

def get_system_prompt() -> str:
    """Single, comprehensive system prompt for all sections."""
    return """You are a professional resume editor. Your job is to improve existing resume content using natural, conversational language.

CORE PRINCIPLES:
1. NEVER add information not in the original content
2. Use simple, natural language - write like a human, not a robot
3. Avoid corporate buzzwords and jargon
4. Keep all dates, numbers, company names exactly the same
5. Only rephrase what already exists
6. Do not use any markdown formatting (**bold**, *italic*, ###headers, etc.) - output plain text only

NATURAL LANGUAGE GUIDELINES:
- Write conversationally: "Worked with clients" not "Interfaced with stakeholders"
- Use everyday words: "helped" not "facilitated", "managed" not "orchestrated"
- Be specific when original is specific, general when original is general
- Start sentences naturally, not always with action verbs

FORBIDDEN WORDS/PHRASES:
- spearheaded, leveraged, orchestrated, synergized, pioneered, revolutionized
- passionate, dedicated, results-driven, dynamic, innovative, cutting-edge
- "proven track record", "showcasing", "demonstrating expertise"

GOOD TRANSFORMATIONS:
- "Responsible for managing team" → "Managed a team of 5 people"
- "Utilized advanced Excel functions" → "Used Excel for data analysis"
- "Spearheaded implementation" → "Led the implementation of..."

Remember: You're making human language more human, not more corporate."""

def get_section_prompt(section: str, content: str, job_description: str = "") -> str:
    """Generate contextual prompt for any section."""
    base_prompt = f"""
SECTION: {section}
ORIGINAL CONTENT: {content}

TASK: Rewrite this content using natural, professional language. Maintain proper formatting and structure.

FORMATTING REQUIREMENTS:
- CRITICAL: Copy the exact formatting structure from the original
- If original has line breaks after job titles/project names, keep them
- If original uses bullet points (- or •), maintain them exactly
- If original has blank lines between sections, preserve them
- Do NOT reformat or reorganize the structure
- Output should look identical to input structure, just with better words

SPECIFIC INSTRUCTIONS FOR {section.upper()}:
"""

    if section.lower() in ['summary', 'profile', 'objective']:
        base_prompt += """
- Write 2-3 clear sentences about what this person does and their experience
- Start with their role or field, not personality adjectives
- Be factual, not promotional
- Keep as paragraph format, not bullet points
"""
    
    elif 'experience' in section.lower() or 'work' in section.lower():
        base_prompt += """
- Keep job titles, companies, and dates on separate lines exactly as shown
- Maintain bullet point format with same indentation
- Keep line breaks between different positions
- Do not merge bullets into paragraphs
- Keep the same number of bullet points
- Preserve spacing and structure exactly
"""
    
    elif 'project' in section.lower():
        base_prompt += """
- Keep project names and core details the same
- Maintain original formatting (bullets, paragraphs, etc.)
- Explain what was built or accomplished in plain language
- Keep separate projects visually separated
- Preserve line breaks and bullet structure exactly
"""
    
    elif 'skill' in section.lower():
        base_prompt += """
- CRITICAL: Keep the exact same formatting as the original
- If original has "- Category: item1, item2, item3" format, keep it exactly
- If original has categories with colons, maintain them
- Do not add or remove dashes, bullets, or line breaks
- Do not reorganize or regroup items
- Simply improve the wording while keeping structure identical
"""
    
    else:
        base_prompt += """
- Maintain the original formatting structure exactly
- Keep bullet points, line breaks, and spacing
- Improve clarity while preserving visual organization
"""

    if job_description:
        base_prompt += f"\nCONTEXT: This is for a role involving: {job_description[:200]}...\nOnly emphasize relevant experience the candidate actually has.\n"

    base_prompt += """

FORMATTING EXAMPLE:
If original looks like:
Job Title
Company, Location
- Bullet point one
- Bullet point two

Your output should look like:
Job Title  
Company, Location
- Improved bullet point one
- Improved bullet point two

CRITICAL: Match the original formatting structure exactly - same line breaks, same bullets, same spacing.

Rewrite the content:"""
    return base_prompt

def clean_markdown_formatting(text: str) -> str:
    """Remove markdown formatting like **bold**, *italic*, ### headers, etc."""

    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()

def rewrite_resume_section(section: str, content: str, full_resume: str, job_description: str = "") -> str:
    """Rewrite a single resume section with validation."""
    if not content.strip():
        return content
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": get_section_prompt(section, content, job_description)}
            ],
            temperature=0.3,
            max_tokens=500,
            presence_penalty=0.3
        )
        
        rewritten = response.choices[0].message.content.strip()

        rewritten = clean_markdown_formatting(rewritten)
        
        validated = validate_against_resume(full_resume, rewritten)

        validation_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Compare original and rewritten content. Return 'VALID' if rewritten only rephrases existing info. Return 'INVALID' if any new information was added."
                },
                {
                    "role": "user",
                    "content": f"ORIGINAL:\n{content}\n\nREWRITTEN:\n{validated}\n\nValidation:"
                }
            ],
            temperature=0.1,
            max_tokens=10
        )
        
        if "INVALID" in validation_response.choices[0].message.content:
            print(f"Warning: Validation failed for {section}. Using original.")
            return content
            
        return validated
        
    except Exception as e:
        print(f"Error rewriting {section}: {e}")
        return content
    
def rewrite_resume(resume_sections: dict, job_description: str = "") -> dict:
    """Main function to rewrite all resume sections."""
    full_resume_text = " ".join(resume_sections.values())
    rewritten_sections = {}

    section_order = ['Summary', 'Profile', 'Objective', 'Experience', 'Work Experience', 
                    'Projects', 'Skills', 'Education', 'Certifications']

    for section in section_order:
        if section in resume_sections:
            print(f"Processing {section}...")
            rewritten_sections[section] = rewrite_resume_section(
                section, resume_sections[section], full_resume_text, job_description
            )

    for section, content in resume_sections.items():
        if section not in rewritten_sections:
            print(f"Processing {section}...")
            rewritten_sections[section] = rewrite_resume_section(
                section, content, full_resume_text, job_description
            )
    
    return rewritten_sections