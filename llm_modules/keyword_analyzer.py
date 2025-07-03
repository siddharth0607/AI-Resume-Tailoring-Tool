from llm_modules.jd_comparator import compare_resume_with_jd
from typing import List
import re

def analyze_ats_keywords(parsed_resume: dict, job_description: str) -> dict:
    """Performs full ATS keyword analysis between resume and job description"""
    jd_analysis = compare_resume_with_jd(parsed_resume, job_description)
    
    if "error" in jd_analysis:
        return {"error": jd_analysis["error"]}

    ats_analysis = {
        "keyword_coverage": calculate_keyword_coverage(jd_analysis),
        "missing_keywords": extract_missing_keywords(jd_analysis),
        "matched_keywords": extract_matched_keywords(jd_analysis),
        "keyword_suggestions": generate_keyword_suggestions(jd_analysis),
        "ats_score": calculate_ats_score(jd_analysis),
        "priority_actions": get_priority_actions(jd_analysis)
    }
    
    return ats_analysis

def calculate_keyword_coverage(jd_analysis: dict) -> dict:
    """Calculates matched and missing keyword coverage metrics"""
    matched_skills = jd_analysis.get("matched_skills", [])
    missing_critical = [
        m for m in jd_analysis.get("missing_critical", [])
        if not is_non_matchable_phrase(m.get("skill", ""))
    ]

    critical_matched = sum(1 for match in matched_skills if match.get("confidence", 0) > 0.7)
    critical_missing = sum(1 for miss in missing_critical if miss.get("importance") == "critical")
    
    important_missing = sum(1 for miss in missing_critical if miss.get("importance") == "important")
    
    total_critical = critical_matched + critical_missing
    total_important = len(matched_skills) + important_missing
    
    return {
        "overall_percentage": jd_analysis.get("overall_assessment", {}).get("match_percentage", 0),
        "critical_coverage": (critical_matched / total_critical * 100) if total_critical > 0 else 0,
        "matched_count": len(matched_skills),
        "missing_count": len(missing_critical),
        "coverage_breakdown": {
            "excellent": critical_matched,
            "needs_improvement": critical_missing,
            "bonus_skills": len(jd_analysis.get("resume_strengths", []))
        }
    }

def generate_inclusion_suggestion(missing_skill: dict) -> str:
    """Suggests where and how to include a missing skill"""
    skill = missing_skill["skill"]
    category = missing_skill.get("category", "")
    
    if category == "technical":
        return f"Include {skill} in your Skills section or project descriptions."
    elif category == "soft_skill":
        return f"Demonstrate {skill} in summary or work experience bullets."
    elif category == "certification":
        return f"Mention {skill} under Certifications or Education."
    else:
        return f"Add {skill} in the most relevant section to showcase your familiarity."
    
NON_MATCHABLE_PATTERNS = [
    r"\b(?:at\s+least|min(?:imum)?|over)?\s*\d+\+?\s*(?:years?|yrs?)\s+of\s+(?:.*?\s+)?experience\b"
    r"\bself[-\s]?starter\b",
    r"\b(?:strong|excellent)\s+(?:communication|presentation)\s+skills\b",
    r"\bagile(?:\s+\w+)?\s+(mindset|thinking|approach|culture|environment)s?\b",
    r"\b(thrive|perform well)\s+in\s+(ambiguity|uncertainty)\b",
    r"\bteam\s+player\b",
    r"\b(?:independent|collaborative|proactive|vocal)\b",
    r"\bresilience|ownership|grit|self[-\s]?driven\b",
    r"\bproblem[-\s]?solver\b",
    r"\bresults[-\s]?driven\b",
    r"\bstrong\s+work\s+ethic\b",
    r"\bworks\s+well\s+under\s+pressure\b",
    r"\bpays\s+attention\s+to\s+detail\b",
    r"\bhighly\s+motivated\b",
    r"\bpunctual\b",
    r"\bpassion(?:ate)?\s+about\b"
]

def is_non_matchable_phrase(text: str) -> bool:
    """Checks if a phrase is generic and not useful for ATS matching"""
    text = text.lower()
    for pattern in NON_MATCHABLE_PATTERNS:
        if re.search(pattern, text):
            return True
    return False

def extract_missing_keywords(jd_analysis: dict) -> List[dict]:
    """Extracts and formats missing keywords with ATS impact and suggestions"""
    missing_critical = jd_analysis.get("missing_critical", [])

    formatted_missing = []
    for missing in missing_critical:
        keyword = missing["skill"]
        if is_non_matchable_phrase(keyword):
            continue

        formatted_missing.append({
            "keyword": keyword,
            "importance": missing["importance"],
            "category": missing["category"],
            "alternatives": missing.get("alternatives", []),
            "ats_impact": get_ats_impact(missing["importance"]),
            "suggestion": generate_inclusion_suggestion(missing)
        })

    priority_order = {"critical": 1, "important": 2, "nice to have": 3}
    formatted_missing.sort(key=lambda x: priority_order.get(x["importance"], 4))

    return formatted_missing

def extract_matched_keywords(jd_analysis: dict) -> List[dict]:
    """Extracts and ranks matched keywords with confidence and match type"""
    matched_skills = jd_analysis.get("matched_skills", [])
    
    formatted_matches = []
    for match in matched_skills:
        formatted_matches.append({
            "keyword": match["skill"],
            "jd_term": match["jd_term"],
            "resume_term": match["resume_term"],
            "match_type": match.get("match_type", "semantic"),
            "confidence": match["confidence"],
            "ats_strength": get_ats_strength(match["confidence"], match["match_type"])
        })

    formatted_matches.sort(key=lambda x: x["confidence"], reverse=True)
    
    return formatted_matches

def generate_keyword_suggestions(jd_analysis: dict) -> List[dict]:
    """Generates actionable suggestions for including missing keywords"""
    suggestions = []
    missing_critical = [
        m for m in jd_analysis.get("missing_critical", [])
        if not is_non_matchable_phrase(m.get("skill", ""))
    ]
    
    for missing in missing_critical[:5]:
        suggestion = {
            "keyword": missing["skill"],
            "where_to_add": suggest_placement(missing),
            "example_phrases": generate_example_phrases(missing),
            "priority": missing["importance"]
        }
        suggestions.append(suggestion)
    
    return suggestions

def calculate_ats_score(jd_analysis: dict) -> dict:
    """Computes ATS score from keyword matching results"""

    matched_skills = jd_analysis.get("matched_skills", [])
    missing_critical = [
        m for m in jd_analysis.get("missing_critical", [])
        if not is_non_matchable_phrase(m.get("skill", ""))
    ]

    exact_matches = sum(1 for match in matched_skills if match.get("match_type") == "exact")
    semantic_matches = sum(1 for match in matched_skills if match.get("match_type") == "semantic")

    critical_matched = sum(1 for match in matched_skills if match.get("confidence", 0) > 0.7)
    critical_missing = sum(1 for miss in missing_critical if miss.get("importance") == "critical")
    
    important_missing = sum(1 for miss in missing_critical if miss.get("importance") == "important")

    total_critical = critical_matched + critical_missing
    critical_score = (critical_matched / total_critical * 100) if total_critical > 0 else 100

    total_keywords = len(matched_skills) + len(missing_critical)
    coverage_score = (len(matched_skills) / total_keywords * 100) if total_keywords > 0 else 100

    total_matches = len(matched_skills)
    quality_bonus = 0
    if total_matches > 0:
        exact_ratio = exact_matches / total_matches
        quality_bonus = exact_ratio * 10
    
    ats_score = (critical_score * 0.6) + (coverage_score * 0.3) + quality_bonus

    if critical_missing > 0:
        penalty = min(20, critical_missing * 5)
        ats_score = max(0, ats_score - penalty)
    
    ats_score = min(100, round(ats_score))
    
    return {
        "ats_score": ats_score,
        "ats_category": get_ats_category(ats_score),
        "exact_matches": exact_matches,
        "semantic_matches": semantic_matches,
        "improvement_potential": 100 - ats_score,
        "score_breakdown": {
            "critical_skills_score": round(critical_score),
            "coverage_score": round(coverage_score),
            "quality_bonus": round(quality_bonus),
            "penalty_applied": critical_missing * 5 if critical_missing > 0 else 0
        }
    }

def get_priority_actions(jd_analysis: dict) -> List[str]:
    """Generates high-priority optimization tips for improving ATS score"""
    actions = []
    missing_critical = [
        m for m in jd_analysis.get("missing_critical", [])
        if not is_non_matchable_phrase(m.get("skill", ""))
    ]

    critical_missing = [m for m in missing_critical if m.get("importance") == "critical"]
    
    if critical_missing:
        actions.append(f"Add {len(critical_missing)} critical keywords: {', '.join([m['skill'] for m in critical_missing[:3]])}")

    matched_skills = jd_analysis.get("matched_skills", [])
    weak_matches = [m for m in matched_skills if m.get("confidence", 0) < 0.6]
    
    if weak_matches:
        actions.append(f"Strengthen {len(weak_matches)} weak keyword matches")

    semantic_only = [m for m in matched_skills if m.get("match_type") == "semantic"]
    if semantic_only:
        actions.append(f"Use exact JD terms for {len(semantic_only)} semantic matches")
    
    return actions[:5]

def get_ats_impact(importance: str) -> str:
    """Returns ATS impact level based on keyword importance"""
    impact_map = {
        "critical": "High - May filter out resume",
        "important": "Medium - Reduces ranking",
        "nice_to_have": "Low - Minimal impact"
    }
    return impact_map.get(importance, "Unknown")

def get_ats_strength(confidence: float, match_type: str) -> str:
    """Determines strength of match for a keyword"""
    if match_type == "exact" and confidence > 0.8:
        return "Strong"
    elif match_type == "semantic" and confidence > 0.7:
        return "Good"
    else:
        return "Weak"

def get_ats_category(score: int) -> str:
    """Categorizes the ATS score into qualitative buckets"""
    if score >= 80:
        return "Excellent - Likely to pass ATS"
    elif score >= 60:
        return "Good - Should pass most ATS"
    elif score >= 40:
        return "Fair - May struggle with strict ATS"
    else:
        return "Poor - Unlikely to pass ATS"

def suggest_placement(missing_skill: dict) -> str:
    """Suggests the best section to add a missing skill"""
    category = missing_skill.get("category", "")
    
    if category == "technical":
        return "Skills section or project descriptions"
    elif category == "soft_skill":
        return "Summary or experience bullets"
    elif category == "certification":
        return "Certifications section or education"
    else:
        return "Most relevant experience section"

def generate_example_phrases(missing_skill: dict) -> List[str]:
    """Generates example resume phrases using a missing skill"""
    skill = missing_skill["skill"]
    category = missing_skill.get("category", "")
    
    if category == "technical":
        return [
            f"Utilized {skill} for data analysis",
            f"Implemented solutions using {skill}",
            f"Experience with {skill} in production environments"
        ]
    elif category == "soft_skill":
        return [
            f"Demonstrated {skill} by leading cross-functional teams",
            f"Applied {skill} to resolve complex challenges",
            f"Leveraged {skill} to improve team performance"
        ]
    else:
        return [
            f"Applied {skill} in professional context",
            f"Gained experience in {skill} through project work",
            f"Developed proficiency in {skill}"
        ]

def get_ats_dashboard_data(parsed_resume: dict, job_description: str) -> dict:
    """One-liner for getting all ATS dashboard data"""
    return analyze_ats_keywords(parsed_resume, job_description)