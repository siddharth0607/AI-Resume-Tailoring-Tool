from resume_parser.parser import fix_spacing
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def simple_fallback_sent_split(text: str) -> list:
    """ Fallback sentence splitter using heuristic chunking for long blocks of resume text"""
    text = re.sub(r"([a-z])([A-Z])", r"\1. \2", text)
    text = re.sub(r"([a-zA-Z])(\d)", r"\1. \2", text)
    text = re.sub(r"([.?!])([A-Z])", r"\1 \2", text)
    words = text.strip().split()
    chunks = [' '.join(words[i:i+15]) for i in range(0, len(words), 15)]
    return [chunk.strip() for chunk in chunks if len(chunk.strip()) > 10]

def extract_resume_content(text: str) -> list:
    """
    Robust content extraction with multiple fallback strategies
    Guarantees returning meaningful content for optimization
    """
    if not text or not text.strip():
        return []

    text = text.strip()

    bullet_pattern = re.compile(r'[\n•\-‣●▪➤▶\*\+]+')
    bullet_candidates = [
        fix_spacing(b.strip()) for b in bullet_pattern.split(text)
        if len(b.strip()) > 15 and not b.strip().startswith('http')
    ]
    
    if len(bullet_candidates) >= 3:
        return bullet_candidates[:15]

    pattern_splits = re.split(r'(?:\n|^)(?=(?:Led|Developed|Managed|Created|Built|Designed|Implemented|Coordinated|Achieved|Improved|Reduced|Increased|Collaborated|Responsible for|Worked on))', text, flags=re.IGNORECASE)
    
    pattern_candidates = [
        fix_spacing(s.strip()) for s in pattern_splits
        if len(s.strip()) > 20 and any(word in s.lower() for word in ['led', 'developed', 'managed', 'created', 'built', 'designed', 'implemented'])
    ]
    
    if len(pattern_candidates) >= 3:
        return pattern_candidates[:12]

    sentences = re.split(r'[.!?]+', text)
    sentence_candidates = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if (len(sentence) > 25 and 
            any(word in sentence.lower() for word in ['experience', 'project', 'skill', 'work', 'develop', 'manage', 'create', 'build', 'lead', 'design', 'implement', 'achieve', 'improve', 'responsible', 'collaborate']) and
            not sentence.lower().startswith(('education', 'degree', 'university', 'college', 'school'))):
            sentence_candidates.append(fix_spacing(sentence))
    
    if len(sentence_candidates) >= 3:
        return sentence_candidates[:10]

    words = text.split()
    if len(words) < 10:
        return [text] if len(text) > 20 else []

    chunk_size = max(15, len(words) // 6)
    chunks = []
    
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i+chunk_size])
        if len(chunk) > 30:
            chunks.append(fix_spacing(chunk))

    if not chunks and len(text) > 20:
        chunks = [text]
    
    return chunks[:8]

def optimize_resume_bullets(parsed_resume: dict, job_description: str) -> dict:
    """Rewrite and optimize resume bullet points based on a given job description"""
    bullet_sections = ["Experience", "Projects", "Achievements", "Internships", "Volunteer", "Work Experience", "Professional Experience", "Technical Projects", "Summary", "Objective"]

    exclude_sections = ["Education", "Contact", "Personal Information", "References", "Languages", "Certifications", "Awards", "Honors", "Publications", "Patents", "Licenses"]
    
    all_bullets = []

    for section in bullet_sections:
        content = None
        for key in parsed_resume.keys():
            if key.lower().replace(' ', '').replace('_', '') == section.lower().replace(' ', '').replace('_', ''):
                content = parsed_resume[key]
                break
        
        if content is None:
            continue
            
        bullets = []

        if isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    extracted = extract_resume_content(item)
                    bullets.extend(extracted)
        elif isinstance(content, str) and content.strip():
            extracted = extract_resume_content(content)
            bullets.extend(extracted)

        all_bullets.extend([(b, section) for b in bullets])

    if len(all_bullets) < 3:
        for section_name, content in parsed_resume.items():
            if any(exclude.lower() in section_name.lower() for exclude in exclude_sections):
                continue
            
            if isinstance(content, str) and len(content.strip()) > 50:
                extracted = extract_resume_content(content)
                all_bullets.extend([(c, section_name) for c in extracted])

    if not all_bullets:
        fallback_content = []
        for section_name, content in parsed_resume.items():
            if any(exclude.lower() in section_name.lower() for exclude in exclude_sections):
                continue
                
            if isinstance(content, str) and len(content.strip()) > 20:
                fallback_content.append((content.strip(), section_name))
        
        if fallback_content:
            all_bullets = fallback_content[:5]
        else:
            optimizable_text = []
            for section_name, content in parsed_resume.items():
                if not any(exclude.lower() in section_name.lower() for exclude in exclude_sections):
                    if isinstance(content, str) and len(content.strip()) > 20:
                        optimizable_text.append(content)
            
            if optimizable_text:
                combined_text = ' '.join(optimizable_text)
                if len(combined_text) > 50:
                    all_bullets = [(combined_text, "general")]

    if not all_bullets:
        return {"error": "No content found in resume for optimization"}

    all_bullets = all_bullets[:20]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional resume editor. Your job is to improve resume bullet points by making them clearer, more specific, and results-focused while keeping them completely authentic.\n\n"
                        "CORE PRINCIPLES:\n"
                        "1. Only improve what's already there - never add fake achievements or exaggerated claims\n"
                        "2. Focus on actions taken and concrete results achieved\n"
                        "3. Use specific, measurable language when possible\n"
                        "4. Write in active voice with strong action verbs\n"
                        "5. Keep the original scope and impact - don't oversell\n"
                        "6. Only improve clarity and structure - never add factual details that weren't in the original text\n\n"
                        "FORBIDDEN PHRASES - NEVER use these generic endings:\n"
                        "- \"demonstrating expertise in...\"\n"
                        "- \"showcasing skills in...\"\n"
                        "- \"leveraging knowledge of...\"\n"
                        "- \"highlighting proficiency in...\"\n"
                        "- \"exhibiting mastery of...\"\n"
                        "- \"displaying competency in...\"\n"
                        "- \"evidencing capabilities in...\"\n\n"
                        "FORBIDDEN PATTERNS:\n"
                        "- Don't end bullets with skill demonstrations\n"
                        "- Don't add generic business buzzwords\n"
                        "- Don't use corporate jargon unnecessarily\n"
                        "- Don't claim expertise unless explicitly stated in original\n"
                        "- Don't add, change, or assume any technical details, company names, tool names, or specific information not in the original\n\n"
                        "GOOD PATTERNS:\n"
                        "- State what you built/created/developed\n"
                        "- Mention specific technologies used\n"
                        "- Include quantifiable results when available\n"
                        "- Focus on business impact or technical outcomes\n"
                        "- Use natural, conversational professional language\n\n"
                        "EXAMPLE TRANSFORMATIONS:\n"
                        "BAD: \"Managed team members showcasing leadership skills\"\n"
                        "GOOD: \"Led 5-person team to complete project 2 weeks ahead of schedule\"\n\n"
                        "BAD: \"Handled customer service demonstrating communication expertise\"\n"
                        "GOOD: \"Resolved 50+ customer inquiries daily, maintaining 95% satisfaction rate\"\n\n"
                        "BAD: \"Organized events leveraging project management knowledge\"\n"
                        "GOOD: \"Coordinated 3 annual conferences for 200+ attendees each\"\n\n"
                        "BAD: \"Analyzed data showcasing analytical capabilities\"\n"
                        "GOOD: \"Analyzed sales trends identifying $50K cost-saving opportunity\"\n\n"
                        "BAD: \"Created content highlighting creative abilities\"\n"
                        "GOOD: \"Produced 20+ blog posts generating 15% increase in website traffic\"\n\n"
                        "Return authentic, professional bullet points that sound like a real person wrote them."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"JOB DESCRIPTION:\n{job_description}\n\n"
                        f"RESUME BULLETS TO IMPROVE:\n" +
                        "\n".join([f"• {bullet}" for bullet, _ in all_bullets]) +
                        "\n\nRewrite these bullets to be more impactful while keeping them authentic. Focus on clarity, specificity, and results. Only incorporate job description keywords if they fit naturally.\n\n"
                        "Return JSON format:\n"
                        "{\n"
                        "  \"optimized_bullets\": [\n"
                        "    {\n"
                        "      \"original\": \"original text\",\n"
                        "      \"optimized\": \"improved text\",\n"
                        "      \"jd_keywords_added\": [\"keyword1\", \"keyword2\"],\n"
                        "      \"improvements\": [\"specific improvement made\"],\n"
                        "      \"impact_score\": 1-10,\n"
                        "      \"section\": \"experience/projects/etc\"\n"
                        "    }\n"
                        "  ],\n"
                        "  \"optimization_summary\": {\n"
                        "    \"total_bullets_processed\": 4,\n"
                        "    \"avg_improvement_score\": 7.5,\n"
                        "    \"key_themes_emphasized\": [\"specific themes\"],\n"
                        "    \"jd_alignment_percentage\": 85\n"
                        "  }\n"
                        "}"
                    )
                }
            ],
            temperature=0.4,
            max_tokens=2500
        )

        result = response.choices[0].message.content.strip()
        if result.startswith('```json'):
            result = result.replace('```json', '').replace('```', '').strip()

        optimized_data = json.loads(result)

        organized_results = {}
        for bullet_data in optimized_data.get("optimized_bullets", []):
            section = bullet_data.get("section", "general")
            if section not in organized_results:
                organized_results[section] = []
            organized_results[section].append(bullet_data)

        return {
            "organized_by_section": organized_results,
            "optimization_summary": optimized_data.get("optimization_summary", {}),
            "all_optimized_bullets": [b["optimized"] for b in optimized_data.get("optimized_bullets", [])],
            "improvement_analysis": optimized_data.get("optimized_bullets", [])
        }

    except json.JSONDecodeError as e:
        return {"error": f"JSON parsing failed: {str(e)}", "raw_response": result}
    except Exception as e:
        return {"error": f"Optimization failed: {str(e)}"}

def get_top_optimized_bullets(optimization_results: dict, top_n: int = 5) -> list:
    """Returns top N optimized bullets with highest impact score"""
    if "improvement_analysis" not in optimization_results:
        return []
    
    bullets = optimization_results["improvement_analysis"]
    sorted_bullets = sorted(bullets, key=lambda x: x.get("impact_score", 0), reverse=True)
    
    return [{
        "optimized_text": bullet["optimized"],
        "impact_score": bullet.get("impact_score", 0),
        "keywords_added": bullet.get("jd_keywords_added", []),
        "improvements": bullet.get("improvements", [])
    } for bullet in sorted_bullets[:top_n]]

def create_optimized_resume_section(optimization_results: dict, section_name: str) -> str:
    """Assembles a clean formatted markdown-style section from optimized bullets"""
    if "organized_by_section" not in optimization_results:
        return f"# {section_name.title()}\nNo optimized content available."
    
    section_data = optimization_results["organized_by_section"].get(section_name, [])
    if not section_data:
        return f"# {section_name.title()}\nNo content found for this section."
    
    formatted_section = f"# {section_name.title()}\n\n"
    for bullet_data in section_data:
        formatted_section += f"• {bullet_data['optimized']}\n"
    
    return formatted_section

def quick_bullet_optimization(parsed_resume: dict, job_description: str) -> list:
    """Fast utility to extract all optimized bullet points as a flat list"""
    results = optimize_resume_bullets(parsed_resume, job_description)
    if "error" in results:
        return [f"Error: {results['error']}"]
    return results.get("all_optimized_bullets", [])