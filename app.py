import streamlit as st
import pdfplumber
from io import StringIO
from docx import Document

# Title for the app
st.title("AI Resume Tailoring Tool")

# File uploader for resume
uploaded_file = st.file_uploader("Upload your resume (PDF or Word)", type=["pdf", "docx"])

# Text input for Job Description
job_description = st.text_area("Paste Job Description")

resume_content = ""
if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            resume_content = ""
            for page in pdf.pages:
                resume_content += page.extract_text()
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        resume_content = ""
        for para in doc.paragraphs:
            resume_content += para.text + "\n"
    
    # Display the extracted resume content
    st.subheader("Resume Content")
    st.text_area("Extracted Resume Text", resume_content, height=200)

# Display the JD input for review
st.subheader("Job Description")
st.text_area("Job Description Text", job_description, height=200)
