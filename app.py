import streamlit as st
import tempfile
import os
from io import BytesIO
from docx import Document
from fpdf import FPDF
from resume_parser.parser import parse_resume_sections, initialize_analyzer
from llm_modules.formatter import format_resume_sections_with_llm
from llm_modules.jd_comparator import compare_resume_with_jd, generate_interview_focus_areas
from llm_modules.bullet_rewriter import optimize_resume_bullets, get_top_optimized_bullets
from llm_modules.keyword_analyzer import analyze_ats_keywords
from utils.field_extractor import extract_fields_from_resume
from llm_modules.cover_letter import generate_cover_letter

st.set_page_config(page_title="AI Resume Tailor", layout="wide")

st.sidebar.title("Navigation")
section = st.sidebar.radio(
    "Go to",
    [
        "Upload Resume & JD",
        "Resume Contents",
        "Resume vs JD Analysis",
        "ATS Report with Resume Suggestions",
        "Generate Cover Letter",
    ]
)

if "parsed" not in st.session_state:
    st.session_state["parsed"] = None
    st.session_state["formatted"] = None
    st.session_state["jd_text"] = None

if section == "Upload Resume & JD":
    st.title("Upload Resume and Job Description")

    uploaded_resume = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

    jd_input_method = st.radio(
        "How would you like to provide the Job Description?",
        ["Paste Job Description", "Upload JD File (.txt)"],
        index=0
    )

    jd_text_input = None
    jd_provided = False

    if jd_input_method == "Paste Job Description":
        jd_text_input = st.text_area(
            "Paste the Job Description below",
            height=250,
            placeholder="Paste the job description you're applying to..."
        )
        jd_provided = bool(jd_text_input.strip())

    elif jd_input_method == "Upload JD File (.txt)":
        uploaded_jd = st.file_uploader("Upload Job Description File (.txt)", type=["txt"])
        if uploaded_jd:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_jd_file:
                tmp_jd_file.write(uploaded_jd.read())
                jd_path = tmp_jd_file.name
            with open(jd_path, "r", encoding="utf-8") as f:
                jd_text_input = f.read()
                jd_provided = True

    if uploaded_resume and jd_provided:
        with st.spinner("Parsing and formatting your resume..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_resume.read())
                resume_path = tmp_file.name

            analyzer = initialize_analyzer()
            parsed = parse_resume_sections(resume_path, analyzer)
            formatted = format_resume_sections_with_llm(parsed)

            st.session_state["parsed"] = parsed
            st.session_state["formatted"] = formatted
            st.session_state["jd_text"] = jd_text_input.strip()

            raw_resume_text = "\n".join(parsed.values())
            st.session_state["extracted_fields"] = extract_fields_from_resume(raw_resume_text)

        st.success("Resume and Job Description processed successfully.")

    elif uploaded_resume and not jd_provided:
        st.info("Please provide the Job Description to continue.")

if section == "Resume Contents":
    st.title("Resume Contents")

    formatted_sections = st.session_state.get("formatted")
    if formatted_sections:
        for formatted_text in formatted_sections.values():
            st.markdown(formatted_text, unsafe_allow_html=True)
    else:
        st.warning("Please upload and process your resume first.")

if section == "Resume vs JD Analysis":
    st.title("Resume vs Job Description Match Report")

    if st.session_state.get("parsed") and st.session_state.get("jd_text"):
        if "jd_comparison_triggered" not in st.session_state:
            st.session_state["jd_comparison_triggered"] = False

        if not st.session_state["jd_comparison_triggered"]:
            if st.button("Run Resume vs JD Analysis"):
                st.session_state["jd_comparison_triggered"] = True
                st.rerun()
        else:
            spinner_container = st.empty()
            with spinner_container:
                with st.spinner("Analyzing Resume vs Job Description..."):
                    result = compare_resume_with_jd(st.session_state["parsed"], st.session_state["jd_text"])

            spinner_container.empty()
            st.session_state["jd_comparison_triggered"] = False

            if "error" in result:
                st.error("Error during JD comparison.")
                st.code(result.get("raw_response", "No response"), language="json")
            else:
                oa = result["overall_assessment"]
                st.subheader("Executive Summary")
                st.markdown(f"""
                **Match Score:** {oa['match_percentage']}%  
                **Fit Level:** {oa['fit_level'].capitalize()}  
                **Recommendation:** {oa['recommendation'].capitalize()}  
                **Summary:** {oa['reasoning']}
                """)

                st.divider()
                st.subheader("Key Strengths")
                for strength in oa["key_strengths"]:
                    st.markdown(f"- {strength}")

                st.subheader("Critical Skill Gaps")
                if result["missing_critical"]:
                    for gap in result["missing_critical"]:
                        st.markdown(f"""
                        - **{gap['skill']}** ({gap['importance']}, {gap['category']})  
                          Alternatives: `{', '.join(gap.get('alternatives', []))}`  
                        """)
                else:
                    st.markdown("No major gaps identified.")

                st.subheader("Matched Skills")
                for match in result["matched_skills"]:
                    st.markdown(f"""
                    - **{match['skill']}**  
                      JD: `{match['jd_term']}` | Resume: `{match['resume_term']}`  
                      Match Type: `{match['match_type']}` | Confidence: `{match['confidence']}`  
                      Reason: {match['reasoning']}
                    """)

                st.subheader("Additional Resume Strengths")
                if result["resume_strengths"]:
                    for s in result["resume_strengths"]:
                        st.markdown(f"- **{s['skill']}** ({s['relevance']}) - {s['value_add']}")
                else:
                    st.markdown("None found.")

                st.subheader("Domain Alignment")
                domain = result["domain_insights"]
                st.markdown(f"""
                - Resume Domain: `{domain['resume_domain']}`  
                - JD Domain: `{domain['jd_domain']}`  
                - Cross-Domain Applicability: `{domain['cross_domain_applicability']}`  
                - Notes: {domain['domain_specific_notes']}
                """)

                st.subheader("Suggested Interview Focus Areas")
                focus_areas = generate_interview_focus_areas(result)
                if focus_areas:
                    for item in focus_areas:
                        st.markdown(f"- {item}")
                else:
                    st.markdown("None generated.")
    else:
        st.warning("Please upload your resume and JD.")

if section == "ATS Report with Resume Suggestions":
    st.title("ATS Report with Resume Suggestions")
    if "bullet_optimization_triggered" not in st.session_state:
        st.session_state["bullet_optimization_triggered"] = False
    if "bullet_optimization_result" not in st.session_state:
        st.session_state["bullet_optimization_result"] = None
    if "ats_analysis_result" not in st.session_state:
        st.session_state["ats_analysis_result"] = None

    if st.session_state.get("formatted") and st.session_state.get("jd_text"):
        if not st.session_state["bullet_optimization_triggered"]:
            if st.button("Run Optimization"):
                st.session_state["bullet_optimization_triggered"] = True
                st.rerun()
        else:
            with st.spinner("Analyzing resume and optimizing bullets..."):
                if not st.session_state["bullet_optimization_result"]:
                    st.session_state["bullet_optimization_result"] = optimize_resume_bullets(
                        st.session_state["formatted"], st.session_state["jd_text"]
                    )
                if not st.session_state["ats_analysis_result"]:
                    st.session_state["ats_analysis_result"] = analyze_ats_keywords(
                        st.session_state["formatted"], st.session_state["jd_text"]
                    )

            optimization_results = st.session_state["bullet_optimization_result"]
            ats_data = st.session_state["ats_analysis_result"]

            if "error" in optimization_results:
                st.error("Bullet optimization failed.")
                st.code(optimization_results["error"])
            elif "error" in ats_data:
                st.error("ATS Analysis failed.")
                st.code(ats_data["error"])
            else:
                st.subheader("ATS Keyword Analysis")
                st.metric("ATS Score", f"{ats_data['ats_score']['ats_score']}%")
                st.caption(ats_data['ats_score']['ats_category'])

                st.markdown("**Top Missing Keywords:**")
                for missing in ats_data["missing_keywords"][:5]:
                    st.markdown(f"- **{missing['keyword']}** ({missing['importance']})")

                st.markdown("**Priority Suggestions:**")
                for action in ats_data["priority_actions"]:
                    st.markdown(f"- {action}")

                st.subheader("Resume Content Suggestions")

                with st.expander("Suggestions by Section"):
                    for section, bullets in optimization_results["organized_by_section"].items():
                        st.markdown(f"### {section.title()}")
                        for b in bullets:
                            st.markdown(
                                f"- **Original:** {b['original']}  \n"
                                f"  **Optimized:** {b['optimized']}  \n"
                                f"  **Keywords:** `{', '.join(b.get('jd_keywords_added', []))}`  \n"
                                f"  **Score:** `{b.get('impact_score', '-')}`  \n"
                                f"  **Improvements:** `{', '.join(b.get('improvements', []))}`"
                            )

                with st.expander("Resume Enhancement Summary"):
                    summary = optimization_results["optimization_summary"]
                    st.markdown(f"- **Total Suggestions Made:** {summary.get('total_bullets_processed', '-')}")
                    st.markdown(f"- **Average Impact Score:** {summary.get('avg_improvement_score', '-')}")
                    st.markdown(f"- **JD Alignment (%):** {summary.get('jd_alignment_percentage', '-')}")
                    st.markdown(f"- **Key Themes Emphasized:** {', '.join(summary.get('key_themes_emphasized', []))}")
    else:
        st.warning("Please upload both resume and job description first.")

if section == "Generate Cover Letter":
    st.title("Tailored Cover Letter Generator")

    if st.session_state.get("formatted") and st.session_state.get("jd_text"):
        name = st.session_state.get("extracted_fields", {}).get("name", "Candidate")

        company_name = st.text_input("Company Name", placeholder="e.g. Google")
        role_title = st.text_input("Role Title", placeholder="e.g. Software Engineer")

        tone_options_display = ["Professional", "Friendly", "Confident", "Enthusiastic", "Conversational"]
        tone_map = {display: display.lower() for display in tone_options_display}

        selected_display = st.selectbox(
            "Tone of the Letter", 
            tone_options_display, 
            index=0, 
            help="Select the desired tone for your cover letter"
        )

        selected_tone = tone_map[selected_display]

        if st.button("Generate Cover Letter"):
            with st.spinner("Generating Cover Letter..."):
                cover_letter = generate_cover_letter(
                    formatted_resume=st.session_state["formatted"],
                    job_description=st.session_state["jd_text"],
                    candidate_name=name,
                    company_name=company_name,
                    role_title=role_title,
                    tone=selected_tone
                )
                st.session_state["cover_letter"] = cover_letter

        if st.session_state.get("cover_letter"):
            st.subheader("Cover Letter Preview")
            st.text_area("", value=st.session_state["cover_letter"], height=400, key="cover_preview")

            export_format = st.radio(
                "Choose export format",
                ["TXT", "PDF", "DOCX"],
                horizontal=True,
                index=0
            )

            if export_format == "TXT":
                st.download_button(
                    label="Download as TXT",
                    data=st.session_state["cover_letter"],
                    file_name="cover_letter.txt",
                    mime="text/plain"
                )

            elif export_format == "PDF":
                from fpdf import FPDF
                import unicodedata

                def clean_text(text):
                    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=12)
                pdf.set_font("Arial", size=11)

                cleaned_text = clean_text(st.session_state["cover_letter"])
                line_height = 6
                for line in cleaned_text.split("\n"):
                    if line.strip():
                        pdf.multi_cell(0, line_height, line)
                    else:
                        pdf.ln(line_height)

                pdf_output = pdf.output(dest="S").encode("latin-1")

                st.download_button(
                    label="Download as PDF",
                    data=pdf_output,
                    file_name="cover_letter.pdf",
                    mime="application/pdf"
                )

            elif export_format == "DOCX":
                from docx import Document
                import io

                doc = Document()
                for line in st.session_state["cover_letter"].split("\n"):
                    doc.add_paragraph(line)

                doc_io = io.BytesIO()
                doc.save(doc_io)
                doc_io.seek(0)

                st.download_button(
                    label="Download as DOCX",
                    data=doc_io,
                    file_name="cover_letter.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
    else:
        st.warning("Please upload both resume and job description first.")