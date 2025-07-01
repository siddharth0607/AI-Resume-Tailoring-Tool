import streamlit as st
import tempfile
from resume_parser.parser import parse_resume_sections, initialize_analyzer
from llm_modules.formatter import format_resume_sections_with_llm
from llm_modules.jd_comparator import compare_resume_with_jd, generate_interview_focus_areas
from llm_modules.bullet_rewriter import optimize_resume_bullets, get_top_optimized_bullets

st.set_page_config(page_title="AI Resume & JD Analyzer", layout="wide")
st.title("AI Resume and Job Description Analyzer")

uploaded_resume = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
uploaded_jd = st.file_uploader("Upload Job Description (TXT)", type=["txt"])

if uploaded_resume:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_resume.read())
        resume_path = tmp_file.name

    st.success("Resume uploaded successfully.")

    analyzer = initialize_analyzer()
    parsed_sections = parse_resume_sections(resume_path, analyzer)
    formatted_sections = format_resume_sections_with_llm(parsed_sections)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Parsed Resume Sections")
        for section, content in parsed_sections.items():
            st.markdown(f"**{section}**")
            st.text_area(label="", value=content, height=150, key=f"parsed_{section}")

    with col2:
        st.subheader("Formatted Resume (LLM Enhanced)")
        for section, content in formatted_sections.items():
            st.markdown(f"**{section}**")
            st.text_area(label="", value=content, height=150, key=f"formatted_{section}")

    st.download_button("Download Parsed Resume", "\n\n".join(f"{k}:\n{v}" for k, v in parsed_sections.items()), "parsed_resume.txt")
    st.download_button("Download Formatted Resume", "\n\n".join(f"{k}:\n{v}" for k, v in formatted_sections.items()), "formatted_resume.txt")

if uploaded_resume and uploaded_jd:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_jd_file:
        tmp_jd_file.write(uploaded_jd.read())
        jd_path = tmp_jd_file.name

    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    st.markdown("---")
    st.subheader("Resume and Job Description Comparison")

    result = compare_resume_with_jd(parsed_sections, jd_text)

    if "error" in result:
        st.error("Error during JD comparison.")
        st.code(result.get("raw_response", "No response"), language="json")
    else:
        st.success(f"Match Level: {result['overall_assessment']['fit_level']} ({result['overall_assessment']['match_percentage']}%)")

        with st.expander("Matched Skills", expanded=True):
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
                    f"  Suggested Alternatives: {', '.join(missing.get('alternatives', []))}"
                )

        with st.expander("Additional Resume Strengths"):
            for strength in result["resume_strengths"]:
                st.markdown(
                    f"- **{strength['skill']}** ({strength['relevance']})  \n"
                    f"  Value Added: {strength['value_add']}"
                )

        with st.expander("Overall Fit Summary"):
            oa = result["overall_assessment"]
            st.markdown(f"- **Match Percentage:** {oa['match_percentage']}%")
            st.markdown(f"- **Fit Level:** {oa['fit_level']}")
            st.markdown(f"- **Key Strengths:** {', '.join(oa['key_strengths'])}")
            st.markdown(f"- **Main Gaps:** {', '.join(oa['main_gaps'])}")
            st.markdown(f"- **Recommendation:** {oa['recommendation']}")
            st.markdown(f"- **Explanation:** {oa['reasoning']}")

        with st.expander("Domain Insights"):
            domain = result["domain_insights"]
            st.markdown(f"- **Resume Domain:** {domain['resume_domain']}")
            st.markdown(f"- **JD Domain:** {domain['jd_domain']}")
            st.markdown(f"- **Cross-domain Applicability:** {domain['cross_domain_applicability']}")
            st.markdown(f"- **Notes:** {domain['domain_specific_notes']}")

        st.markdown("---")
        st.subheader("Suggested Interview Focus Areas")
        focus_areas = generate_interview_focus_areas(result)
        for item in focus_areas:
            st.markdown(f"- {item}")

        st.markdown("---")
        st.subheader("Bullet Point Optimization")

        optimization_results = optimize_resume_bullets(formatted_sections, jd_text)

        if "error" in optimization_results:
            st.error("Bullet optimization failed.")
            st.code(optimization_results["error"])
        else:
            with st.expander("Optimized Bullets by Section", expanded=True):
                for section, bullets in optimization_results["organized_by_section"].items():
                    st.markdown(f"#### {section.capitalize()}")
                    for b in bullets:
                        st.markdown(
                            f"- **Original:** {b['original']}  \n"
                            f"  **Optimized:** {b['optimized']}  \n"
                            f"  Keywords Added: `{', '.join(b.get('jd_keywords_added', []))}`  \n"
                            f"  Impact Score: `{b.get('impact_score', '-')}`  \n"
                            f"  Improvements: `{', '.join(b.get('improvements', []))}`"
                        )

            with st.expander("Top 5 Most Improved Bullets"):
                top_bullets = get_top_optimized_bullets(optimization_results)
                for i, b in enumerate(top_bullets, 1):
                    st.markdown(
                        f"**{i}.** {b['optimized_text']}  \n"
                        f"Impact Score: `{b['impact_score']}` | Keywords: `{', '.join(b['keywords_added'])}`"
                    )

            with st.expander("Optimization Summary"):
                summary = optimization_results["optimization_summary"]
                st.markdown(f"- **Total Bullets Processed:** {summary.get('total_bullets_processed', '-')}")
                st.markdown(f"- **Average Impact Score:** {summary.get('avg_improvement_score', '-')}")
                st.markdown(f"- **JD Alignment (%):** {summary.get('jd_alignment_percentage', '-')}")
                st.markdown(f"- **Key Themes:** {', '.join(summary.get('key_themes_emphasized', []))}")
