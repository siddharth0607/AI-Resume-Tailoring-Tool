from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_cover_letter(formatted_resume: dict, job_description: str, candidate_name: str = "Candidate", company_name: str = "the company") -> str:
    """"Generate a personalized cover letter using resume content and job description"""
    resume_text = "\n\n".join(f"{section}:\n{content}" for section, content in formatted_resume.items())
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert career coach who writes exceptional cover letters that get interviews. "
                        "Create compelling, personalized cover letters that:\n"
                        "- Open with a strong hook that shows genuine interest and knowledge about the company\n"
                        "- Tell a story that connects the candidate's experience to the role's requirements\n"
                        "- Use specific examples and quantifiable achievements\n"
                        "- Show enthusiasm and cultural fit\n"
                        "- End with a confident call-to-action\n"
                        "- Sound authentic and human, not generic or robotic\n"
                        "- Are concise but impactful (3-4 paragraphs max)"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Write a standout cover letter for {candidate_name} applying to {company_name}.\n\n"
                        f"JOB DESCRIPTION:\n{job_description}\n\n"
                        f"CANDIDATE'S RESUME:\n{resume_text}\n\n"
                        "INSTRUCTIONS:\n"
                        "1. Research what makes this company unique and reference it in the opening\n"
                        "2. Identify the top 3 most relevant qualifications from the resume\n"
                        "3. Create a narrative that connects past achievements to future impact\n"
                        "4. Use specific metrics, numbers, or results where available\n"
                        "5. Show personality while maintaining professionalism\n"
                        "6. Make the hiring manager excited to meet this candidate\n"
                        "7. Address it to 'Hiring Manager' and skip contact details/date"
                    )
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error generating cover letter: {str(e)}]"