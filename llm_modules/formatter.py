from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def format_resume_sections_with_llm(sections: dict) -> dict:
    formatted_sections = {}

    for section, content in sections.items():
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert resume formatter. Your job is to take messy or unstructured resume content "
                            "and convert it into clean, well-formatted, professional-looking text. "
                            "Use proper spacing, punctuation, and consistent styling. "
                            "Convert lists of skills or achievements into bullet points if needed."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Please clean up and professionally format the following resume section.\n\n"
                            f"Section Title: {section}\n\n"
                            f"Raw Content:\n{content}\n\n"
                            "Make sure to:\n"
                            "- Add missing spaces between words or sentences.\n"
                            "- Format any inline skills, tools, or items into readable bullets or inline lists where appropriate.\n"
                            "- Keep section-specific formatting conventions (e.g., jobs in Experience should show role, org, date).\n"
                            "- Do NOT hallucinate or add any new content — only reformat what's provided.\n"
                            "- Use markdown-style bullet points if the content is list-like.\n"
                            "- Expand or display full URLs, don't truncate them.\n"
                            "- Do not end lines or bullet points with ellipses (...), unless it's intentional or a continuation.\n"
                            "- Preserve structured items such as degrees, institutions, job titles, and durations clearly.\n"
                            "- If a section like 'CGPA' or 'Scores' looks like it belongs to 'Education', merge or nest it under Education.\n"
                            "- If a section is titled 'Technologies', 'Tools', or 'Software', reclassify and format it under 'Skills'. Do not create a new section.\n"
                        )
                    }
                ],
                temperature=0.5,
                max_tokens=1000
            )
            formatted_text = response.choices[0].message.content.strip()
            formatted_sections[section] = formatted_text

        except Exception as e:
            formatted_sections[section] = f"[Error formatting section:\n\n{e}\n]"

    return formatted_sections