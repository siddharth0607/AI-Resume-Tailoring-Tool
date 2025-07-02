import streamlit as st
import tempfile
from resume_parser.parser import parse_resume_sections, initialize_analyzer
from llm_modules.formatter import format_resume_sections_with_llm
from llm_modules.jd_comparator import compare_resume_with_jd, generate_interview_focus_areas
from llm_modules.bullet_rewriter import optimize_resume_bullets, get_top_optimized_bullets
from utils.field_extractor import extract_fields_from_resume
from llm_modules.cover_letter import generate_cover_letter
from llm_modules.resume_rewriter import rewrite_resume
from utils.pdf_exporter import export_to_pdf

st.set_page_config(page_title="AI Resume Tailor", layout="wide")

st.sidebar.title("Navigation")
section = st.sidebar.radio(
    "Go to",
    [
        "Upload Resume & JD",
        "View Resume Sections",
        "LLM-Formatted Resume",
        "Resume vs JD Analysis",
        "Bullet Point Optimization",
        "Generate Cover Letter",
        "Tailored Resume (Rewritten)"
    ]
)
rewrite_toggle = st.sidebar.checkbox("Enable JD-Aware Resume Rewrite")

if "parsed" not in st.session_state:
    st.session_state["parsed"] = None
    st.session_state["formatted"] = None
    st.session_state["jd_text"] = None

if section == "Upload Resume & JD":
    st.title("Upload Your Resume and Job Description")

    uploaded_resume = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    uploaded_jd = st.file_uploader("Upload Job Description (TXT)", type=["txt"])

    if uploaded_resume:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_resume.read())
            resume_path = tmp_file.name

        analyzer = initialize_analyzer()
        parsed = parse_resume_sections(resume_path, analyzer)
        formatted = format_resume_sections_with_llm(parsed)

        st.session_state["parsed"] = parsed
        st.session_state["formatted"] = formatted
        st.success("Resume parsed and formatted successfully.")

        raw_resume_text = "\n".join(st.session_state["parsed"].values())
        extracted_fields = extract_fields_from_resume(raw_resume_text)

        st.session_state["extracted_fields"] = extracted_fields

    if uploaded_jd:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_jd_file:
            tmp_jd_file.write(uploaded_jd.read())
            jd_path = tmp_jd_file.name

        with open(jd_path, "r", encoding="utf-8") as f:
            st.session_state["jd_text"] = f.read()

if section == "View Resume Sections":
    st.title("Parsed Resume Sections")
    if st.session_state["parsed"]:
        for section, content in st.session_state["parsed"].items():
            st.markdown(f"**{section}**")
            st.text_area(label="", value=content, height=150, key=f"parsed_{section}")
    else:
        st.warning("Please upload your resume first.")

if section == "LLM-Formatted Resume":
    st.title("LLM-Enhanced Resume Formatting")
    if st.session_state["formatted"]:
        for section, content in st.session_state["formatted"].items():
            st.markdown(f"### {section}")
            st.markdown(content, unsafe_allow_html=True)

    else:
        st.warning("Resume not formatted yet.")

if section == "Resume vs JD Analysis":
    st.title("Resume vs JD Semantic Analysis")
    if st.session_state.get("parsed") and st.session_state.get("jd_text"):
        resume_data = {
            "parsed": st.session_state["parsed"],
            "formatted": st.session_state.get("formatted")
        }
        result = compare_resume_with_jd(resume_data, st.session_state["jd_text"])

        if "error" in result:
            st.error("Error during JD comparison.")
            st.code(result.get("raw_response", "No response"), language="json")
        else:
            st.success(f"Fit Level: {result['overall_assessment']['fit_level']} ({result['overall_assessment']['match_percentage']}%)")

            with st.expander("Matched Skills"):
                for match in result["matched_skills"]:
                    st.markdown(
                        f"- **{match['skill']}** (JD: {match['jd_term']} / Resume: {match['resume_term']})  \n"
                        f"  Match Type: `{match['match_type']}` | Confidence: `{match['confidence']}`  \n"
                        f"  Reason: {match['reasoning']}"
                    )

            with st.expander("Missing Critical Skills"):
                for missing in result["missing_critical"]:
                    st.markdown(
                        f"- **{missing['skill']}** ({missing['importance']}, {missing['category']})  \n"
                        f"  Alternatives: {', '.join(missing.get('alternatives', []))}"
                    )

            with st.expander("Additional Resume Strengths"):
                for strength in result["resume_strengths"]:
                    st.markdown(
                        f"- **{strength['skill']}** ({strength['relevance']})  \n"
                        f"  Value Add: {strength['value_add']}"
                    )

            with st.expander("Overall Fit Summary"):
                oa = result["overall_assessment"]
                st.markdown(f"- **Match Percentage:** {oa['match_percentage']}%")
                st.markdown(f"- **Fit Level:** {oa['fit_level']}")
                st.markdown(f"- **Key Strengths:** {', '.join(oa['key_strengths'])}")
                st.markdown(f"- **Main Gaps:** {', '.join(oa['main_gaps'])}")
                st.markdown(f"- **Recommendation:** {oa['recommendation']}")
                st.markdown(f"- **Reasoning:** {oa['reasoning']}")

            with st.expander("Domain Insights"):
                domain = result["domain_insights"]
                st.markdown(f"- **Resume Domain:** {domain['resume_domain']}")
                st.markdown(f"- **JD Domain:** {domain['jd_domain']}")
                st.markdown(f"- **Cross-domain Applicability:** {domain['cross_domain_applicability']}")
                st.markdown(f"- **Domain Notes:** {domain['domain_specific_notes']}")

            st.subheader("Suggested Interview Focus Areas")
            focus_areas = generate_interview_focus_areas(result)
            for item in focus_areas:
                st.markdown(f"- {item}")
    else:
        st.warning("Upload both Resume and Job Description first.")

if section == "Bullet Point Optimization":
    st.title("Optimized Bullet Points")
    if st.session_state["formatted"] and st.session_state["jd_text"]:
        optimization_results = optimize_resume_bullets(st.session_state["formatted"], st.session_state["jd_text"])

        if "error" in optimization_results:
            st.error("Bullet optimization failed.")
            st.code(optimization_results["error"])
        else:
            with st.expander("Optimized Bullets by Section"):
                for section, bullets in optimization_results["organized_by_section"].items():
                    st.markdown(f"**{section.title()}**")
                    for b in bullets:
                        st.markdown(
                            f"- **Original:** {b['original']}  \n"
                            f"  **Optimized:** {b['optimized']}  \n"
                            f"  Keywords: `{', '.join(b.get('jd_keywords_added', []))}`  \n"
                            f"  Score: `{b.get('impact_score', '-')}`  \n"
                            f"  Improvements: `{', '.join(b.get('improvements', []))}`"
                        )

            with st.expander("Top 5 Most Improved Bullets"):
                top_bullets = get_top_optimized_bullets(optimization_results)
                for i, b in enumerate(top_bullets, 1):
                    st.markdown(
                        f"**{i}.** {b['optimized_text']}  \n"
                        f"Score: `{b['impact_score']}` | Keywords: `{', '.join(b['keywords_added'])}`"
                    )

            with st.expander("Optimization Summary"):
                summary = optimization_results["optimization_summary"]
                st.markdown(f"- **Total Bullets:** {summary.get('total_bullets_processed', '-')}")
                st.markdown(f"- **Average Score:** {summary.get('avg_improvement_score', '-')}")
                st.markdown(f"- **JD Alignment (%):** {summary.get('jd_alignment_percentage', '-')}")
                st.markdown(f"- **Key Themes:** {', '.join(summary.get('key_themes_emphasized', []))}")
    else:
        st.warning("Please upload both Resume and JD.")

if section == "Generate Cover Letter":
    st.title("AI-Generated Cover Letter")

    if st.session_state.get("formatted") and st.session_state.get("jd_text"):
        name = st.session_state.get("extracted_fields", {}).get("name", "Candidate")

        company_name = st.text_input("Company Name", value="the company")
        role_title = st.text_input("Role Title", value="this position")

        tone_options = ["professional", "friendly", "confident", "enthusiastic", "conversational"]
        tone = st.selectbox("Tone of the Letter", tone_options, index=0)

        if st.button("Generate Cover Letter"):
            with st.spinner("Generating..."):
                cover_letter = generate_cover_letter(
                    formatted_resume=st.session_state["formatted"],
                    job_description=st.session_state["jd_text"],
                    candidate_name=name,
                    company_name=company_name,
                    role_title=role_title,
                    tone=tone
                )
                st.text_area("Cover Letter", value=cover_letter, height=400)
                st.download_button("Download Cover Letter", cover_letter, file_name="cover_letter.txt")
    else:
        st.warning("Please upload both resume and job description first.")

if section == "Tailored Resume (Rewritten)":
    st.title("Tailored Resume Based on JD")

    if st.session_state.get("formatted") and st.session_state.get("jd_text"):
        if rewrite_toggle:
            with st.spinner("Rewriting your resume with JD context..."):
                rewritten = rewrite_resume(
                    resume_sections=st.session_state["formatted"],
                    job_description=st.session_state["jd_text"]
                )
                st.session_state["rewritten"] = rewritten
                st.success("Resume tailored successfully.")
        else:
            st.info("Enable the rewrite toggle in the sidebar to generate tailored resume.")

        if "rewritten" in st.session_state:
            for section_name, rewritten_content in st.session_state["rewritten"].items():
                st.markdown(f"### {section_name}")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Original:**")
                    st.text_area("", st.session_state["formatted"].get(section_name, ""), height=180)
                with col2:
                    st.markdown("**Rewritten:**")
                    st.text_area("", rewritten_content, height=180, key=f"rewritten_{section_name}")

            st.markdown("---")
            st.subheader("Export Tailored Resume as PDF")
            template_choice = st.selectbox("Choose Template", ["modern.html"])
            if st.button("Download Tailored Resume as PDF"):
                pdf_bytes = export_to_pdf(st.session_state["rewritten"], template_choice)
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name="Tailored_Resume.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("No rewritten content found.")
    else:
        st.warning("Please upload your resume and job description first.")