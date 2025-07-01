from openai import OpenAI
import os
import re
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BANNED_WORDS = [
    'spearheaded', 'leveraged', 'orchestrated', 'synergized', 'pioneered', 
    'championed', 'revolutionized', 'architected', 'strategized', 'optimized',
    'streamlined', 'innovative', 'cutting-edge', 'state-of-the-art', 'robust', 
    'scalable', 'dynamic', 'dedicated', 'passionate', 'motivated', 'driven', 
    'results-driven', 'proven track record', 'showcasing', 'demonstrating', 
    'expertise', 'adept', 'seasoned', 'accomplished', 'exceptional'
]

FIELD_APPROPRIATE_WORDS = ['facilitated', 'coordinated', 'collaborated', 'proficient']

def extract_key_facts(original_content: str) -> dict:
    """Extract key facts from original resume to validate against."""
    facts = {
        'years_mentioned': re.findall(r'\b(\d+)\s*(?:years?|yrs?)\b', original_content.lower()),
        'dates': re.findall(r'\b(20\d{2}|19\d{2})\b', original_content),
        'numbers': re.findall(r'\b\d+\b', original_content),
        'percentages': re.findall(r'\b\d+%\b', original_content),
        'dollar_amounts': re.findall(r'\$[\d,]+', original_content)
    }
    return facts

def validate_output(original_content: str, rewritten_content: str, section: str) -> str:
    """Validate that rewritten content doesn't add fake information."""

    banned_for_check = [word for word in BANNED_WORDS if word not in FIELD_APPROPRIATE_WORDS]
    
    for word in banned_for_check:
        if word.lower() in rewritten_content.lower():
            replacements = {
                'spearheaded': 'led', 'leveraged': 'used', 'orchestrated': 'managed',
                'synergized': 'worked with', 'pioneered': 'started', 'championed': 'supported',
                'revolutionized': 'improved', 'architected': 'designed', 'strategized': 'planned',
                'optimized': 'improved', 'streamlined': 'simplified', 'innovative': 'new',
                'cutting-edge': 'advanced', 'state-of-the-art': 'modern', 'robust': 'strong',
                'scalable': 'flexible', 'dynamic': 'active', 'dedicated': '', 'passionate': '',
                'motivated': '', 'driven': '', 'results-driven': '', 'showcasing': 'showing',
                'demonstrating': 'showing', 'expertise': 'experience', 'adept': 'skilled',
                'seasoned': 'experienced', 'accomplished': 'experienced', 'exceptional': 'strong'
            }
            replacement = replacements.get(word.lower(), 'worked on')
            rewritten_content = re.sub(r'\b' + word + r'\b', replacement, rewritten_content, flags=re.IGNORECASE)

    original_years = set(re.findall(r'\b(\d+)\s*(?:years?|yrs?)\b', original_content.lower()))
    rewritten_years = set(re.findall(r'\b(\d+)\s*(?:years?|yrs?)\b', rewritten_content.lower()))

    if rewritten_years - original_years:
        print(f"WARNING: New years of experience detected in {section}. Removing...")
        for year in rewritten_years - original_years:
            pattern = rf'\b{year}\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)\b'
            rewritten_content = re.sub(pattern, '', rewritten_content, flags=re.IGNORECASE)
    
    return rewritten_content.strip()

def detect_resume_field(resume_sections: dict) -> str:
    """Detect the field/industry of the resume for context."""
    all_text = " ".join([
        resume_sections.get("Summary", ""),
        resume_sections.get("Experience", ""),
        resume_sections.get("Projects", ""),
        resume_sections.get("Skills", ""),
        resume_sections.get("Education", "")
    ]).lower()

    field_indicators = {
        'technology': ['software', 'developer', 'programming', 'python', 'javascript', 'react', 'aws', 'database', 'api', 'code'],
        'healthcare': ['patient', 'medical', 'hospital', 'clinical', 'nurse', 'doctor', 'healthcare', 'treatment', 'diagnosis'],
        'finance': ['financial', 'accounting', 'investment', 'banking', 'budget', 'revenue', 'audit', 'portfolio', 'trading'],
        'marketing': ['marketing', 'campaign', 'brand', 'social media', 'advertising', 'content', 'seo', 'analytics', 'digital'],
        'sales': ['sales', 'client', 'customer', 'revenue', 'quota', 'lead', 'pipeline', 'negotiation', 'account'],
        'education': ['teacher', 'student', 'curriculum', 'classroom', 'teaching', 'education', 'academic', 'research'],
        'engineering': ['engineering', 'design', 'manufacturing', 'construction', 'mechanical', 'electrical', 'civil'],
        'legal': ['legal', 'law', 'attorney', 'lawyer', 'court', 'litigation', 'contract', 'compliance'],
        'hr': ['human resources', 'recruiting', 'hiring', 'employee', 'training', 'benefits', 'payroll', 'hr'],
        'consulting': ['consulting', 'consultant', 'strategy', 'analysis', 'client', 'advisory', 'recommendations']
    }
    
    field_scores = {}
    for field, keywords in field_indicators.items():
        score = sum(1 for keyword in keywords if keyword in all_text)
        if score > 0:
            field_scores[field] = score
    
    if field_scores:
        return max(field_scores, key=field_scores.get)
    return 'general'

def rewrite_resume_sections_with_llm(resume_sections: dict, job_description: str) -> dict:
    """
    Rewrites resume sections using GPT-4o with field-aware validation.
    """
    rewritten = {}

    resume_field = detect_resume_field(resume_sections)

    available_sections = [key for key, value in resume_sections.items() if value and value.strip()]
    target_sections = ["Summary"] + [s for s in available_sections if s != "Summary"]
    
    for section in target_sections:
        original_content = resume_sections.get(section, "").strip()

        if not original_content and section != "Summary":
            continue

        original_facts = extract_key_facts(original_content) if original_content else {}
            
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": get_universal_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": get_universal_section_prompt(section, original_content, job_description, resume_sections, resume_field)
                    }
                ],
                temperature=0.1,
                max_tokens=400,
                presence_penalty=0.5
            )
            
            raw_output = response.choices[0].message.content.strip()
            validated_output = validate_output(original_content if original_content else "", raw_output, section)

            if section == "Summary" and not original_content:
                all_resume_text = " ".join([v for k, v in resume_sections.items() if k != "Summary" and v])
                
                if all_resume_text.strip():
                    validation_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a fact-checker. Check if the generated summary only mentions information that exists in the resume sections. If ANY information was invented, return 'INVALID'. If it only summarizes existing information, return 'VALID'."
                            },
                            {
                                "role": "user",
                                "content": f"RESUME SECTIONS:\n{all_resume_text}\n\nGENERATED SUMMARY:\n{validated_output}\n\nDoes the summary only mention what's in the resume sections?"
                            }
                        ],
                        temperature=0.1,
                        max_tokens=10
                    )
                    
                    if "INVALID" in validation_response.choices[0].message.content:
                        print(f"WARNING: Generated summary contains invalid information. Creating basic summary.")
                        rewritten[section] = create_universal_summary(resume_sections, resume_field)
                    else:
                        rewritten[section] = validated_output
                else:
                    rewritten[section] = create_universal_summary(resume_sections, resume_field)
            
            elif original_content:
                validation_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a fact-checker. Compare the rewritten resume section with the original. If ANY information was added that wasn't in the original, return 'INVALID'. If it only rephrases existing information, return 'VALID'."
                        },
                        {
                            "role": "user",
                            "content": f"ORIGINAL:\n{original_content}\n\nREWRITTEN:\n{validated_output}\n\nIs the rewritten version valid?"
                        }
                    ],
                    temperature=0.1,
                    max_tokens=10
                )
                
                if "INVALID" in validation_response.choices[0].message.content:
                    print(f"WARNING: Validation failed for {section}. Using original content.")
                    rewritten[section] = original_content
                else:
                    rewritten[section] = validated_output
            else:
                rewritten[section] = validated_output
            
        except Exception as e:
            print(f"Error rewriting {section}: {str(e)}")
            rewritten[section] = original_content
    
    return rewritten

def get_universal_system_prompt() -> str:
    """Universal system prompt that works across all fields."""
    return """You are a professional resume editor who improves wording without adding information.

ABSOLUTE RULES - VIOLATION WILL RESULT IN REJECTION:
1. NEVER add years of experience not explicitly stated in original
2. NEVER add skills, achievements, or responsibilities not in original  
3. NEVER use excessive corporate buzzwords like: spearheaded, leveraged, orchestrated, synergized, revolutionized, innovative, cutting-edge, passionate, dedicated, results-driven
4. NEVER invent dates, numbers, percentages, or company names
5. NEVER claim experience with tools/skills not mentioned in original

APPROPRIATE ACTION VERBS FOR ANY FIELD:
- General: managed, led, created, developed, built, designed, handled, organized, implemented, maintained
- Collaboration: worked with, collaborated, coordinated, facilitated, partnered
- Achievement: achieved, completed, delivered, executed, performed, produced, accomplished
- Analysis: analyzed, evaluated, assessed, reviewed, monitored, tracked, measured
- Communication: presented, communicated, trained, taught, guided, advised

YOUR ONLY JOB:
- Rephrase existing content with clearer, more professional language
- Fix grammar and formatting issues
- Use job-relevant keywords ONLY if they describe existing experience
- Maintain the same factual content and meaning

VERIFICATION: Before responding, ask yourself: "Did I add ANY information not in the original?" If yes, start over."""

def get_universal_section_prompt(section: str, original_content: str, job_description: str, all_resume_sections: dict, resume_field: str) -> str:
    """Generate field-aware prompts for any resume section."""
    
    jd_keywords = extract_universal_keywords(job_description, resume_field)
    
    if section == "Summary":
        return get_universal_summary_prompt(original_content, all_resume_sections, jd_keywords, resume_field)
    
    if section in ["Experience", "Work Experience", "Professional Experience"]:
        return f"""
TASK: Improve the wording of work experience entries.

ORIGINAL CONTENT: {original_content}

JOB CONTEXT: This role involves: {jd_keywords}
FIELD: {resume_field}

RULES:
- Keep all dates, companies, job titles exactly the same
- Only rephrase existing responsibilities and achievements
- Use professional action verbs appropriate for {resume_field}
- Don't add new accomplishments or responsibilities
- Maintain all specific numbers, percentages, and metrics from original

Rewrite the experience section:"""
    
    elif section in ["Projects", "Key Projects", "Notable Projects"]:
        return f"""
TASK: Improve project descriptions.

ORIGINAL CONTENT: {original_content}

JOB CONTEXT: Role involves: {jd_keywords}
FIELD: {resume_field}

RULES:
- Keep project names and core technologies/methods the same
- Only improve descriptions of existing work
- Maintain any metrics or outcomes already mentioned
- Don't add new features, technologies, or results

Rewrite the projects section:"""
    
    elif section in ["Skills", "Technical Skills", "Core Competencies", "Key Skills"]:
        return f"""
TASK: Reorganize and present existing skills better.

ORIGINAL CONTENT: {original_content}

JOB CONTEXT: Role requires: {jd_keywords}
FIELD: {resume_field}

RULES:
- Only list skills already mentioned in original
- Group related skills logically
- Prioritize job-relevant skills the candidate already has
- Don't add new tools, languages, or competencies

Rewrite the skills section:"""
    
    else:
        return f"""
TASK: Improve the presentation of this resume section.

SECTION: {section}
ORIGINAL CONTENT: {original_content}

JOB CONTEXT: Role involves: {jd_keywords}
FIELD: {resume_field}

RULES:
- Only rephrase and reorganize existing information
- Use professional language appropriate for {resume_field}
- Don't add new information not present in original
- Maintain all factual details (dates, names, numbers)

Rewrite this section:"""

def create_universal_summary(resume_sections: dict, resume_field: str) -> str:
    """Create a basic summary for any field when AI generation fails."""

    sections_by_length = sorted(
        [(k, v) for k, v in resume_sections.items() if v and k != "Summary"], 
        key=lambda x: len(x[1]), 
        reverse=True
    )
    
    if not sections_by_length:
        return "Professional seeking opportunities in their field of expertise."

    field_templates = {
        'technology': "Software professional with experience in development and technical projects.",
        'healthcare': "Healthcare professional with clinical and patient care experience.",
        'finance': "Finance professional with experience in financial analysis and management.",
        'marketing': "Marketing professional with experience in campaigns and brand management.",
        'sales': "Sales professional with experience in client relations and revenue generation.",
        'education': "Education professional with teaching and academic experience.",
        'engineering': "Engineering professional with design and technical project experience.",
        'legal': "Legal professional with experience in law and regulatory compliance.",
        'hr': "Human Resources professional with experience in employee relations and organizational development.",
        'consulting': "Consulting professional with experience in analysis and client advisory services.",
        'general': "Professional with diverse experience and proven track record."
    }
    
    return field_templates.get(resume_field, field_templates['general'])

def get_universal_summary_prompt(original_summary: str, all_resume_sections: dict, jd_keywords: str, resume_field: str) -> str:
    """Generate field-aware summary prompt."""

    other_sections = {k: v for k, v in all_resume_sections.items() if k != "Summary" and v}
    sections_text = "\n".join([f"{k}: {v[:300]}..." for k, v in other_sections.items()])

    field_examples = {
        'technology': {
            'good': "Software Engineer at ABC Corp developing web applications. Experience with React, Python, and cloud deployment. Built projects including e-commerce platform and data analytics dashboard.",
            'bad': "Passionate software engineer dedicated to creating innovative solutions..."
        },
        'healthcare': {
            'good': "Registered Nurse at City Hospital with 3 years experience in emergency care. Skilled in patient assessment, medication administration, and electronic health records. Certified in CPR and trauma response.",
            'bad': "Dedicated healthcare professional passionate about patient care..."
        },
        'finance': {
            'good': "Financial Analyst at Investment Firm with experience in portfolio analysis and risk assessment. Skilled in Excel, SQL, and financial modeling. Managed portfolios worth $2M+ and reduced risk exposure by 15%.",
            'bad': "Results-driven finance professional with proven track record..."
        },
        'general': {
            'good': "Marketing Manager at Tech Startup with 4 years experience in digital campaigns. Skilled in Google Analytics, social media management, and content creation. Increased brand engagement by 40% and managed $100K+ budgets.",
            'bad': "Dynamic marketing professional passionate about driving results..."
        }
    }
    
    examples = field_examples.get(resume_field, field_examples['general'])
    
    if original_summary:
        return f"""
TASK: Rewrite this existing summary using simple, professional language.

ORIGINAL SUMMARY: {original_summary}

SUPPORTING SECTIONS FOR CONTEXT:
{sections_text}

CONTEXT: Job seeks someone with: {jd_keywords}
FIELD: {resume_field}

RULES FOR REWRITING:
- Use simple, direct statements appropriate for {resume_field}
- Avoid buzzwords: dedicated, passionate, results-driven, dynamic, innovative, motivated
- Write factually, not emotionally
- 2-3 short, professional sentences
- Start with their actual role/title, not personality adjectives

GOOD Example for {resume_field}: "{examples['good']}"
BAD Example: "{examples['bad']}"

Rewrite the summary:"""
    else:
        return f"""
TASK: Create a simple, factual summary based on the candidate's actual resume content.

RESUME SECTIONS TO BASE SUMMARY ON:
{sections_text}

CONTEXT: Job seeks someone with: {jd_keywords}
FIELD: {resume_field}

RULES FOR WRITING:
- Write 2-3 simple, factual sentences appropriate for {resume_field}
- NO personality adjectives: dedicated, passionate, motivated, driven, innovative
- NO buzzwords: leveraging, spearheading, showcasing, results-driven
- Start with their actual job title/role if available
- State facts: what they do, what they know, what they accomplished
- Write professionally but naturally

GOOD Example for {resume_field}: "{examples['good']}"
BAD Example: "{examples['bad']}"

Create a summary based ONLY on the resume content provided:"""

def extract_universal_keywords(job_description: str, resume_field: str) -> str:
    """Extract relevant keywords from job description based on detected field."""

    field_keywords = {
        'technology': ['python', 'javascript', 'react', 'node', 'sql', 'aws', 'docker', 'git', 'api', 'database', 'cloud', 'agile', 'testing'],
        'healthcare': ['patient care', 'clinical', 'medical', 'healthcare', 'nursing', 'treatment', 'diagnosis', 'electronic health records', 'compliance'],
        'finance': ['financial analysis', 'accounting', 'budgeting', 'forecasting', 'excel', 'financial modeling', 'risk management', 'compliance', 'audit'],
        'marketing': ['digital marketing', 'social media', 'content creation', 'seo', 'analytics', 'campaign management', 'brand management', 'advertising'],
        'sales': ['sales', 'client relations', 'lead generation', 'crm', 'negotiation', 'account management', 'pipeline management', 'customer service'],
        'education': ['curriculum', 'teaching', 'student assessment', 'classroom management', 'educational technology', 'lesson planning', 'academic'],
        'engineering': ['design', 'manufacturing', 'project management', 'cad', 'quality control', 'technical documentation', 'problem solving'],
        'legal': ['legal research', 'contract review', 'compliance', 'litigation', 'legal writing', 'regulatory', 'documentation'],
        'hr': ['recruiting', 'employee relations', 'training', 'benefits administration', 'hr policies', 'performance management', 'onboarding'],
        'consulting': ['analysis', 'strategy', 'client management', 'problem solving', 'presentation', 'project management', 'research']
    }

    relevant_keywords = field_keywords.get(resume_field, [])

    general_keywords = ['communication', 'leadership', 'project management', 'teamwork', 'analysis', 'problem solving', 'microsoft office']
    
    all_keywords = relevant_keywords + general_keywords

    found_terms = []
    jd_lower = job_description.lower()
    
    for term in all_keywords:
        if term.lower() in jd_lower:
            found_terms.append(term)
    
    return ', '.join(found_terms[:10])