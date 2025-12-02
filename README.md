# 🤖 Recruitment Agent

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-CC--BY--SA--4.0-orange.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![Live Demo](https://img.shields.io/badge/Demo-Live-success.svg)](https://recruitment-agent-frontend.onrender.com)

AI-powered resume screening system using Google Gemini 2.0 Flash for automated ATS scoring, skill matching, and candidate evaluation with email notifications.

---

## 🎯 Features

- **Multi-Stage AI Evaluation**: ATS scoring (1-100), dimensional matching (skills, experience, role fit), weighted final scoring
- **Automated Email Notifications**: Instant candidate feedback via MailerSend
- **Modern Web Interface**: React + Vite with real-time processing updates
- **Production Ready**: Deployed on Render.com with rate limit handling
- **Supported Roles**: ML Engineer, Agentic AI Engineer, Software Developer, Data Engineer

## 🚀 Live Demo

**Frontend:** https://recruitment-agent-frontend.onrender.com  
**Backend API:** https://recruitment-agent-backend.onrender.com

---

## 🏗️ Architecture

PDF Upload → Text Extraction → ATS Checker (1-100) →
Per-Dimension Scoring (skill/experience/role/cert) →
Final Score + Contact Extraction → Email Notification → JSON Result

text

**Scoring Formula:**
Final Score = (0.50 × Skill) + (0.20 × Experience) +
(0.15 × Role) + (0.10 × ATS/100) + (0.05 × Cert)

text

---

## 🛠️ Tech Stack

**Backend:** Python 3.9+, Flask, Google Gemini 2.0 Flash, PyPDF2, MailerSend  
**Frontend:** React 18, Vite  
**Deployment:** Render.com

---

## 💻 Quick Start

### Prerequisites
- Python 3.9+, Node.js 16+
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)
- [MailerSend API Key](https://www.mailersend.com/)

### 1. Clone Repository
git clone https://github.com/kandakatlasatwik/recruitment-agent.git
cd recruitment-agent

text

### 2. Backend Setup
Create virtual environment
python -m venv .venv

Activate (Windows)
.venv\Scripts\activate

Activate (Mac/Linux)
source .venv/bin/activate

Install dependencies
pip install -r requirements.txt

text

### 3. Configure Environment
Create `.env` in project root:
GEMINI_API_KEY=your_gemini_api_key_here
MAILERSEND_API_KEY=your_mailersend_api_key_here
MAILERSEND_FROM_EMAIL=noreply@yourdomain.com

text

### 4. Run Locally
Start backend
python app.py

In another terminal - start frontend
cd frontend
npm install
npm run dev

text

**Backend:** http://localhost:5000  
**Frontend:** http://localhost:5173

---

## 📡 API Endpoints

### Health Check
GET /api/health

text

### Get Job Roles
GET /api/job-roles

text

### Process Resume
POST /api/process
Content-Type: multipart/form-data

Body:

file (PDF, required)

job_role (string, required)

candidate_name (optional)

candidate_email (optional)

candidate_linkedin (optional)

text

**Response Example:**
{
"status": "processed",
"meets_ats_threshold": true,
"candidate_info": {
"name": "John Doe",
"email": "john@example.com",
"phone": "+1234567890"
},
"ats_check": {
"score": 85,
"recommendation": "Strong ML background",
"strong_point": "Advanced Python skills",
"weak_point": "Limited production experience"
},
"dimension_scores": {
"skill_match": 0.92,
"experience_match": 0.65,
"role_match": 0.88,
"certification_bonus": 0.40
},
"final_score": 0.823,
"email_sent": true
}

text

---

## 🌐 Deployment to Render

### Backend
1. Push code to GitHub
2. Create **Web Service** on Render
3. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. Add environment variables:
   - `GEMINI_API_KEY`
   - `MAILERSEND_API_KEY`
   - `MAILERSEND_FROM_EMAIL`

### Frontend
1. Update `frontend/.env.production`:
VITE_API_URL=https://your-backend-url.onrender.com

text
2. Create **Static Site** on Render
3. Configure:
- **Build Command:** `cd frontend && npm install && npm run build`
- **Publish Directory:** `frontend/dist`

---

## 📁 Project Structure

recruitment-agent/
├── agent.py # Main AI pipeline
├── app.py # Flask REST API
├── email_service.py # Email notifications
├── requirements.txt # Python dependencies
├── .env # Environment variables
└── frontend/ # React app
├── src/
├── package.json
└── vite.config.js

text

---

## 🐛 Troubleshooting

**API Key Not Found:** Ensure `.env` exists with correct keys (no quotes)  
**Rate Limits:** System auto-retries; wait a few minutes  
**CORS Errors:** Update `app.py` with your frontend URL  
**VS Code Environment:** `Ctrl+Shift+P` → "Python: Select Interpreter" → choose `.venv`

---

## 📄 License

**CC-BY-SA 4.0** - Free to use, modify, and distribute commercially. Must credit original authors and share derivatives under same license.

[View License](https://creativecommons.org/licenses/by-sa/4.0/)

---

## 👥 Contributors

- [Satwik Kandakatla](https://github.com/kandakatlasatwik)
- [Vishnu18-tech](https://github.com/Vishnu18-tech)

---

## 📊 Languages

![Python 68.2%](https://img.shields.io/badge/Python-68.2%25-blue) ![JavaScript 18.5%](https://img.shields.io/badge/JavaScript-18.5%25-yellow) ![CSS 12.7%](https://img.shields.io/badge/CSS-12.7%25-purple)

---

<div align="center">
  <p>⭐ Star this repo if you find it helpful!</p>
</div>