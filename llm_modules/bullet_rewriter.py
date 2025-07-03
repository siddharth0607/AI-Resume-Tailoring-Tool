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
    """Uses GPT-4o to rewrite and optimize resume bullet points based on a given job description"""
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
                        "You are an elite resume optimization specialist. Your job is to rewrite resume bullet points "
                        "to maximize alignment with job descriptions while maintaining 100% authenticity.\n\n"
                        "OPTIMIZATION PRINCIPLES:\n"
                        "1. Use JD keywords naturally\n"
                        "2. Improve clarity and results\n"
                        "3. Quantify impact if possible\n"
                        "4. Use strong action verbs\n"
                        "5. Don't fabricate experience\n"
                        "\nReturn JSON with optimized bullets, reasons, and keywords added."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"JOB DESCRIPTION:\n{job_description}\n\n"
                        f"RESUME BULLETS TO OPTIMIZE:\n" +
                        "\n".join([f"• {bullet}" for bullet, _ in all_bullets]) +
                        "\n\nReturn JSON:\n"
                        "{\n"
                        "  \"optimized_bullets\": [\n"
                        "    {\n"
                        "      \"original\": \"original bullet\",\n"
                        "      \"optimized\": \"improved bullet\",\n"
                        "      \"jd_keywords_added\": [\"keyword1\", \"keyword2\"],\n"
                        "      \"improvements\": [\"clearer impact\", \"added result\"],\n"
                        "      \"impact_score\": 1-10,\n"
                        "      \"section\": \"projects\" or \"experience\"\n"
                        "    }\n"
                        "  ],\n"
                        "  \"optimization_summary\": {\n"
                        "    \"total_bullets_processed\": 4,\n"
                        "    \"avg_improvement_score\": 7.5,\n"
                        "    \"key_themes_emphasized\": [\"machine learning\", \"cloud\"],\n"
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