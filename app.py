import streamlit as st
import pdfplumber
from io import StringIO
from docx import Document
from langchain_community.llms import Ollama
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
import json
import re

# Title for the app
st.title("AI Resume Tailoring Tool")

# File uploader for resume
uploaded_file = st.file_uploader("Upload your resume (PDF or Word)", type=["pdf", "docx"])

# Text input for Job Description
job_description = st.text_area("Paste Job Description")

# Function to extract resume information using the LLM
def extract_resume_info(resume_text):
    prompt = PromptTemplate(
    input_variables=["resume_text"],
    template="""
        You are an expert resume parser. Carefully analyze the following resume text and extract key structured information. Return a valid JSON object with the following keys and formats:

        - skills: List of technical or professional skills (e.g., Python, Graphic Design, Financial Modeling).
        - tools_and_technologies: List of software tools, platforms, libraries, databases, etc. (e.g., Excel, TensorFlow, Figma, Salesforce).
        - job_titles: Actual positions or roles held (e.g., Data Science Intern, Event Coordinator). Do not include certifications or project titles.
        - experience_summary: 2–5 concise bullet points summarizing past roles, internships, leadership experiences, or volunteer work. You may infer experience from action verbs, responsibilities, or project context (e.g., "Led a team", "Built an API", "Coordinated a fest", etc).
        - education: A dictionary with:
            - school_name
            - degree_title
            - start_year (YYYY-MM)
            - end_year (YYYY-MM)
            - cgpa (if available)
        - certifications: List of dictionaries. Extract both formal and online learning credentials. Each should include:
            - course
            - provider (e.g., Coursera, Google, Udemy)
        - projects: List of dictionaries, each with:
            - title
            - description
            - metric (if any, e.g., accuracy, revenue, growth, user reach)
        - achievements: Academic, extracurricular, or professional recognitions (e.g., Dean's List, Hackathon Finalist).
        - soft_skills: Personal qualities or team skills (e.g., leadership, communication, adaptability).
        - languages: Human languages (e.g., English, Spanish). Do NOT include programming languages.

        If a section is not present, return an empty list or dictionary for that field. Do not return extra commentary.

        Resume Text:
        {resume_text}
        """
    )



    llm = Ollama(model="deepseek-r1:1.5b")
    chain = LLMChain(llm=llm, prompt=prompt)

    response = chain.run(resume_text)

    # Extract JSON block from response using regex
    match = re.search(r"\{.*\}", response, re.DOTALL)
    if match:
        try:
            json_data = json.loads(match.group())
            return json_data
        except json.JSONDecodeError:
            return {"error": "JSON found but failed to parse"}
    else:
        return {"error": "Failed to find JSON in LLM response", "raw_output": response}

# Extract resume content
resume_content = ""
if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                resume_content += page.extract_text()
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        for para in doc.paragraphs:
            resume_content += para.text + "\n"

    # Display the extracted resume content
    st.subheader("Resume Content")
    st.text_area("Extracted Resume Text", resume_content, height=200)

    # Trigger the resume info extraction
    if resume_content:
        st.subheader("🔍 Extracted Resume Info")
        with st.spinner("Analyzing resume with DeepSeek..."):
            extracted_info = extract_resume_info(resume_content)

            if "error" in extracted_info:
                st.error(extracted_info["error"])
                st.subheader("🔎 Raw Output")
                st.code(extracted_info.get("raw_output", ""), language="json")
            else:
                st.json(extracted_info)

# Display the JD input for review
st.subheader("Job Description")
st.text_area("Job Description Text", job_description, height=200)