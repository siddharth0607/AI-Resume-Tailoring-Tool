from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def compare_resume_with_jd(parsed_resume: dict, job_description: str) -> dict:
    """
    Advanced resume-JD comparison that handles cross-domain relevance,
    semantic matching, and nuanced skill assessment across all industries.
    """
    from openai import OpenAI
    from dotenv import load_dotenv
    import os, json
    
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    resume_text = "\n\n".join(f"{section}:\n{content}" for section, content in parsed_resume.items())
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an elite talent acquisition specialist with deep expertise across all industries "
                        "(tech, finance, healthcare, marketing, operations, design, manufacturing, consulting, etc.). "
                        "Your role is to perform sophisticated resume-JD matching that goes beyond keyword matching.\n\n"
                        
                        "CORE PRINCIPLES:\n"
                        "1. SEMANTIC INTELLIGENCE: Recognize when different terms mean the same thing (e.g., 'JavaScript' vs 'JS', 'Project Management' vs 'Program Coordination')\n"
                        "2. CROSS-DOMAIN RELEVANCE: Identify when skills from one domain apply to another (e.g., statistical analysis for marketing analytics, SQL for business intelligence)\n"
                        "3. CONTEXTUAL UNDERSTANDING: Consider the level, depth, and application context of skills\n"
                        "4. TRANSFERABLE SKILLS: Recognize universally valuable skills (leadership, problem-solving, communication)\n"
                        "5. DOMAIN EXPERTISE: Understand industry-specific tools, methodologies, and career progressions\n\n"
                        
                        "ADVANCED MATCHING LOGIC:\n"
                        "- If JD mentions 'data analysis' and resume has 'statistical modeling' → MATCH\n"
                        "- If JD requires 'cloud experience' and resume shows 'AWS/Azure/GCP' → MATCH\n"
                        "- If JD needs 'customer service' and resume has 'client relationship management' → MATCH\n"
                        "- If JD wants 'automation' and resume shows 'Python scripting for workflows' → MATCH\n"
                        "- Consider certifications relevant to the domain even if not explicitly mentioned\n"
                        "- Recognize when experience level aligns with role requirements\n\n"
                        
                        "EVALUATION FRAMEWORK:\n"
                        "- Technical skills: Exact matches, similar technologies, transferable concepts\n"
                        "- Soft skills: Leadership, communication, teamwork, problem-solving\n"
                        "- Industry knowledge: Domain-specific understanding, regulations, processes\n"
                        "- Tools & platforms: Direct matches, equivalent alternatives, related ecosystems\n"
                        "- Certifications: Relevant credentials, even if not explicitly required\n"
                        "- Experience depth: Junior/mid/senior level alignment"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"JOB DESCRIPTION:\n{job_description}\n\n"
                        f"RESUME CONTENT:\n{resume_text}\n\n"
                        
                        "Perform a comprehensive analysis and return a JSON with these exact keys:\n\n"
                        
                        "{\n"
                        "  \"matched_skills\": [\n"
                        "    {\n"
                        "      \"skill\": \"skill name\",\n"
                        "      \"jd_term\": \"how it appears in JD\",\n"
                        "      \"resume_term\": \"how it appears in resume\",\n"
                        "      \"match_type\": \"exact|semantic|transferable|domain_relevant\",\n"
                        "      \"confidence\": 0.0-1.0,\n"
                        "      \"reasoning\": \"why this is a match\"\n"
                        "    }\n"
                        "  ],\n"
                        "  \"missing_critical\": [\n"
                        "    {\n"
                        "      \"skill\": \"missing skill\",\n"
                        "      \"importance\": \"critical|important|nice_to_have\",\n"
                        "      \"category\": \"technical|soft_skill|certification|experience\",\n"
                        "      \"alternatives\": [\"potential alternatives candidate might have\"]\n"
                        "    }\n"
                        "  ],\n"
                        "  \"resume_strengths\": [\n"
                        "    {\n"
                        "      \"skill\": \"additional skill\",\n"
                        "      \"relevance\": \"highly_relevant|somewhat_relevant|transferable\",\n"
                        "      \"value_add\": \"how this benefits the role\"\n"
                        "    }\n"
                        "  ],\n"
                        "  \"overall_assessment\": {\n"
                        "    \"match_percentage\": 0-100,\n"
                        "    \"fit_level\": \"excellent|good|moderate|poor\",\n"
                        "    \"key_strengths\": [\"top 3 alignment points\"],\n"
                        "    \"main_gaps\": [\"top 3 missing elements\"],\n"
                        "    \"recommendation\": \"proceed|conditional|pass\",\n"
                        "    \"reasoning\": \"detailed explanation of the assessment\"\n"
                        "  },\n"
                        "  \"domain_insights\": {\n"
                        "    \"resume_domain\": \"identified domain\",\n"
                        "    \"jd_domain\": \"job domain\",\n"
                        "    \"cross_domain_applicability\": \"high|medium|low\",\n"
                        "    \"domain_specific_notes\": \"relevant observations\"\n"
                        "  }\n"
                        "}\n\n"
                        
                        "CRITICAL INSTRUCTIONS:\n"
                        "- Be generous with semantic matching but rigorous with accuracy\n"
                        "- Consider the seniority level and adjust expectations accordingly\n"
                        "- Identify domain-relevant certifications even if not explicitly mentioned in JD\n"
                        "- Recognize when someone has deeper expertise in related areas\n"
                        "- Account for industry transitions and transferable skills\n"
                        "- Provide actionable insights in your reasoning\n"
                        "- Ensure the JSON is valid and complete"
                    )
                }
            ],
            temperature=0.2,
            max_tokens=2000
        )
        
        json_response = response.choices[0].message.content.strip()
        
        if json_response.startswith('```json'):
            json_response = json_response.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(json_response)
        
        result['analysis_metadata'] = {
            'model_used': 'gpt-4o',
            'analysis_type': 'comprehensive_semantic_matching',
            'timestamp': str(os.getenv('TIMESTAMP', 'unknown')),
            'resume_sections_analyzed': list(parsed_resume.keys())
        }
        
        return result
        
    except json.JSONDecodeError as e:
        return {
            "error": "JSON parsing failed",
            "raw_response": json_response,
            "json_error": str(e)
        }
    except Exception as e:
        return {
            "error": "Analysis failed",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


def get_domain_specific_insights(resume_analysis: dict) -> dict:
    """
    Extract domain-specific insights and recommendations from the analysis.
    """
    if 'error' in resume_analysis:
        return {"error": "Cannot analyze due to upstream error"}
    
    insights = {
        "skill_gaps_priority": [],
        "certification_recommendations": [],
        "experience_enhancement_areas": [],
        "career_progression_notes": []
    }
    
    if 'missing_critical' in resume_analysis:
        for missing in resume_analysis['missing_critical']:
            if missing['importance'] == 'critical':
                insights['skill_gaps_priority'].append({
                    'skill': missing['skill'],
                    'urgency': 'high',
                    'learning_path': 'immediate_focus'
                })
    
    if 'domain_insights' in resume_analysis:
        domain_info = resume_analysis['domain_insights']
        insights['domain_transition_notes'] = {
            'from_domain': domain_info.get('resume_domain', 'unknown'),
            'to_domain': domain_info.get('jd_domain', 'unknown'),
            'transition_feasibility': domain_info.get('cross_domain_applicability', 'unknown'),
            'specific_notes': domain_info.get('domain_specific_notes', '')
        }
    
    return insights


def generate_interview_focus_areas(resume_analysis: dict) -> list:
    """
    Generate focused interview topics based on the resume analysis.
    """
    if 'error' in resume_analysis:
        return ["General interview due to analysis error"]
    
    focus_areas = []
    
    if 'matched_skills' in resume_analysis:
        high_confidence_matches = [
            match for match in resume_analysis['matched_skills']
            if match.get('confidence', 0) > 0.8
        ]
        
        for match in high_confidence_matches[:3]:
            focus_areas.append(f"Deep dive into {match['skill']} - {match['reasoning']}")
    
    if 'missing_critical' in resume_analysis:
        critical_gaps = [
            gap for gap in resume_analysis['missing_critical']
            if gap['importance'] == 'critical'
        ]
        
        for gap in critical_gaps[:2]:
            focus_areas.append(f"Assess adaptability for {gap['skill']} - explore {gap.get('alternatives', ['related experience'])}")
    
    if 'resume_strengths' in resume_analysis:
        unique_strengths = [
            strength for strength in resume_analysis['resume_strengths']
            if strength['relevance'] in ['highly_relevant', 'transferable']
        ]
        
        for strength in unique_strengths[:2]:
            focus_areas.append(f"Leverage {strength['skill']} - {strength['value_add']}")
    
    return focus_areas[:6]