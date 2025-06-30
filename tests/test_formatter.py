# tests/test_formatting_pipeline.py

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from resume_parser.parser import (
    initialize_analyzer,
    parse_resume_sections
)
from llm_modules.formatter import format_resume_sections_with_llm
import os

# Set your resume file path
resume_pdf_path = "./assets/resume_1.pdf"  # Change path if needed

def test_resume_formatting_pipeline():
    # 1. Initialize parser
    analyzer = initialize_analyzer()

    # 2. Parse resume into sections
    parsed_sections = parse_resume_sections(resume_pdf_path, analyzer)
    
    print("\n🔍 Extracted Sections:")
    for section, content in parsed_sections.items():
        print(f"\n--- {section} ---\n{content[:200]}...")  # Print first 200 chars per section

    # 3. Format the extracted sections using GPT-4o
    formatted_sections = format_resume_sections_with_llm(parsed_sections)

    print("\n✨ Formatted Sections (GPT-4o):")
    for section, content in formatted_sections.items():
        print(f"\n--- {section} ---\n{content[:200]}...")  # Print first 200 chars per section

if __name__ == "__main__":
    test_resume_formatting_pipeline()
