Setup Instructions
1. Clone the Repository
bash
git clone https://github.com/kandakatlasatwik/recruitment-agent.git
cd recruitment-agent
2. Install Python & VS Code Prerequisites
Python: 3.9 or above

VS Code: Install Python Extension

3. Set up a Virtual Environment
bash
python -m venv .venv
# Windows:
.venv\Scripts\activate

4. Install Dependencies
bash
pip install -r requirements.txt
Or, manually:

bash
pip install google-adk google-genai PyPDF2 python-dotenv
5. Configure Environment Variables
Copy your Google Gemini API key.

Create a file called .env in the project root:

text
GEMINI_API_KEY=your-actual-api-key-here
(No quotes, no spaces around the =)

Usage
1. Single PDF Processing
Edit and run agent.py with your PDF file and role:

python
pipeline = RecruitmentPipeline(ats_threshold=70)
result = pipeline.process_application(
    pdf_path="sample_resume.pdf",         # Replace with your PDF file
    job_role="Machine Learning Engineer", # Choose any defined role
    candidate_name="John Doe",            # (optional) for output merging
    candidate_email="john@example.com",   # (optional)
    candidate_linkedin="linkedin.com/in/johndoe" # (optional)
)
Output will be saved as recruitment_result.json.

You can change the job role to "Agentic AI Engineer", "Software Developer", or "Data Engineer".

Run in Terminal
bash
python agent.py
2. Batch Processing (Multiple PDFs)
To analyze all resumes in a folder:

Place all resumes in, e.g., ./resumes/

Use a batch script (see examples in previous explanations) to loop through all .pdf files and call process_application.

3. Custom Configuration
Score Threshold: Change ats_threshold in RecruitmentPipeline(ats_threshold=THRESHOLD)

Model: Uses gemini-1.5-flash for optimal API reliability

Project Structure
text
recruitment-agent/
├── .env                  # API keys (not checked into git)
├── .gitignore
├── .venv/                # Python virtual environment
├── agent.py              # Main logic (edit/run this)
├── requirements.txt      # Dependencies
├── recruitment_result.json # Example output
└── resumes/              # (optional) Folder for batch resumes
Troubleshooting
GEMINI_API_KEY not found: Ensure .env is present and not wrapped in quotes.

Quota or API errors: Free tier API has usage limits. Wait and retry or check your API dashboard.

PDF not found error: Double-check your file path.

Schema validation errors: Make sure your agent.py uses "type": "string" for all schema definitions in the code.

VS Code not detecting environment: Press Ctrl+Shift+P → "Python: Select Interpreter" → choose .venv.

