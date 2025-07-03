# AI Resume Tailoring Tool

**AI Resume Tailoring Tool** is an intelligent assistant that helps job seekers tailor their resumes and cover letters to match specific job descriptions using OpenAI's GPT-4o model. Built with a focus on clarity, performance and ATS alignment, it combines resume parsing, semantic JD comparison, keyword optimization and LLM-assisted rewriting in a clean Streamlit interface.

---

## 🚀 Live Demo

👉 **Try it here:** [AI Resume Tailoring Tool on Hugging Face](https://huggingface.co/spaces/siddharth0607/ai-resume-app)

No installation needed - runs fully in the browser.

---

## 🚀 Key Features

- **Resume Parsing:** Extracts and structures data from PDF resumes.
- **JD Comparison:** Analyzes alignment between resume and job description using semantic matching.
- **Bullet Point Rewriter:** Rewrites resume bullets to align with job-specific terminology and impact.
- **ATS Keyword Analyzer:** Calculates ATS compatibility, missing keywords and score breakdown.
- **Cover Letter Generator:** Generates personalized cover letters based on resume and JD context.
- **Streamlit Web App:** Simple interface to upload files, view results and export updates.

---

## 🎯 Why This Project

Most job seekers submit a one-size-fits-all resume that doesn’t pass through Applicant Tracking Systems (ATS).
This tool helps candidates:
- Understand what’s missing.
- Rephrase content to match job expectations.
- Stand out with personalized, data-backed documents.

Whether you're a student, a junior developer or a working professional, this project makes resume tailoring accessible, fast, and accurate.

---

## 🛠️ Tech Stack

| Layer        | Technology                         |
|--------------|-------------------------------------|
| Language     | Python 3.10+                        |
| Frontend     | Streamlit                          |
| LLMs         | OpenAI GPT-4o /                     |
| Parsing      | pdfplumber, python-docx             |
| PDF Export   | fpdf                                |
| NLP          | Custom Prompt Engineering + Regex   |

---

## 📂 Project Structure

```plaintext
AI-Resume-Tailoring-Tool/
|
|-- app.py                    # Main Streamlit application
|-- requirements.txt          # Project dependencies
|
|-- utils/
|   |-- field_extractor       # Extracts basic contact info (name, phone, email)
|
|-- resume_parser/            
|   |-- parser.py             # Parses resume files
|
|-- llm_modules/
|   |-- bullet_rewriter.py    # Rewrites resume bullet points using GPT-4o
|   |-- cover_letter.py       # Generates tailored cover letters (optional)
|   |-- formatter.py          # Cleans and standardizes parsed content using GPT-4o
|   |-- jd_comparator.py      # Analyzes resume vs. job description alignment
|   |-- keyword_analyzer.py   # Provides ATS-style keyword analysis and suggestions
```

---

## ⚙️ Installation

1. Clone the repository:
   ```
   git clone https://siddharth/AI-Resume-Tailoring-Tool.git
   cd AI-Resume-Tailoring-Tool
   ```

2. Create a virtual environment:
   ```
   python3 -m venv venv
   ```
3. Activate the virtual environment:
   ```
   # On Windows
   .\venv\Scripts\activate

   # On Linux/macOS
   source venv/bin/activate
   ```

4. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Configure OpenAI: 
   Create a `.env` file with your API key:
   ```
   OPENAI_API_KEY=your-key-here
   ```

---

## 🧪 Usage

1. Launch the Streamlit App:
   ```
   streamlit run app.py
   ```

2. Upload your Resume and Job Description

3. Explore Tabs:
   - `Resume Contents`
   - `Resume vs JD Analysis`
   - `ATS Report with Resume Suggestions`
   - `Generate Cover Letter`

---

## 🛡️ Privacy First

- No resume data is stored or logged.
- Your files are processed locally and API calls are made securely.

---

## 🤝 Contributing
Pull requests, issues, and suggestions are welcome! Please open an issue for significant changes or feature requests.
