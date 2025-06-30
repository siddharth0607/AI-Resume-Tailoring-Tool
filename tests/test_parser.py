import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from resume_parser.parser import (
    initialize_analyzer,
    parse_resume_sections,
    get_section_summary,
    debug_parse_resume
)

pdf_path = "assets/resume_1.pdf"

print("Initializing parser...")
analyzer = initialize_analyzer()

print("Debug parsing to see what's happening...")
sections = debug_parse_resume(pdf_path, analyzer)

print("\nParsed Resume Sections:")
for section, content in sections.items():
    print(f"\n--- {section} ---")
    print(f"Content: {content[:200]}...")

summary = get_section_summary(sections)
print("\nSection Word Counts:")
for sec, count in summary.items():
    print(f"{sec}: {count} words")