import os
import json
import time
import re
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from google import genai
from google.genai import types
from email_service import EmailService

load_dotenv()

class RecruitmentPipeline:
    """Main recruitment pipeline with ATS scoring, job matching, and final scoring"""

    def __init__(self, ats_threshold: int = 70, model_name: str = "gemini-2.0-flash"):
        """
        Initialize the pipeline with Gemini client

        Args:
            ats_threshold: Minimum ATS score to continue (default 70)
            model_name: Name of the Gemini model to use
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.ats_threshold = ats_threshold

        self.job_roles = [
            "Machine Learning Engineer",
            "Agentic AI Engineer",
            "Software Developer",
            "Data Engineer",
        ]

        print("✅ Pipeline initialized")
        print(f"✅ ATS Threshold: {self.ats_threshold}/100\n")

    @staticmethod
    def _safe_parse_text_to_json(text: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Try to parse JSON from a string. If full parse fails, attempt to extract
        the first JSON object-looking substring using regex.
        """
        if not text:
            return None
        
        try:
            return json.loads(text)
        except Exception:
            
            match = re.search(r"\{[\s\S]*?\}", text)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    return None
            return None

    def _call_gemini_with_retry(self, prompt: str, config: types.GenerateContentConfig, max_retries: int = 4):
        """
        Call Gemini API with exponential backoff on rate-limit or transient errors.
        Returns the raw response object from the SDK.
        """
        base_wait = 1.0
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config,
                )
                return response
            except Exception as e:
                err = str(e)
                print(f"⚠️ API call failed (attempt {attempt}/{max_retries}): {err}")
                if "429" in err or "RESOURCE_EXHAUSTED" in err or "rate limit" in err.lower():
                    wait_time = base_wait * (2 ** (attempt - 1))
                    
                    m = re.search(r"retry in ([\d.]+)s", err)
                    if m:
                        wait_time = float(m.group(1))
                    if attempt < max_retries:
                        print(f"⏳ Rate-limited. Waiting {wait_time:.1f}s before retry...")
                        time.sleep(wait_time + 0.5)
                        continue
                
                raise
        raise RuntimeError("Failed to get response after retries")

    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF resume

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text content
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            reader = PdfReader(str(path))
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n".join(text_parts).strip()
        except Exception as e:
            raise Exception(f"Error extracting PDF: {e}")

    def ats_checker(self, resume_text: str, job_role: str) -> Dict[str, Any]:
        """
        ATS Checker Agent - Analyzes resume compatibility

        Returns a dict with keys:
          - ats_score (int 1-100)
          - recommendation (string, max 50 words)
          - strong_point (string)
          - weak_point (string)
        """
        system_message = f"""Analyze the resume for the role: {job_role}.

Return output strictly in JSON format only.

Your analysis must include:
- ats_score (integer 1–100)
- recommendation (max 50 words)
- strong_point (1 clear strength of the candidate)
- weak_point (1 clear weakness or missing area relevant to the role)

Be concise and base your judgment only on the resume content. Do NOT add explanations outside the JSON.
"""

        prompt = f"{system_message}\n\nResume:\n{resume_text[:3000]}"

        try:
            response = self._call_gemini_with_retry(
                prompt=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "ats_score": {"type": "integer"},
                            "recommendation": {"type": "string"},
                            "strong_point": {"type": "string"},
                            "weak_point": {"type": "string"},
                        },
                        "required": ["ats_score", "recommendation", "strong_point", "weak_point"],
                    },
                ),
            )

            
            text = getattr(response, "text", None) or getattr(response, "content", None) or str(response)
            parsed = self._safe_parse_text_to_json(text)
            if not parsed:
                print("⚠️ Could not parse ATS JSON response; returning default.")
                return {"ats_score": 0, "recommendation": "Unable to parse ATS result", "strong_point": "", "weak_point": ""}

            
            result = {
                "ats_score": int(parsed.get("ats_score", 0)),
                "recommendation": parsed.get("recommendation") or parsed.get("Recommendation") or "",
                "strong_point": parsed.get("strong_point") or parsed.get("strongPoint") or "",
                "weak_point": parsed.get("weak_point") or parsed.get("weakPoint") or "",
            }

            print(f"✓ ATS Checker completed - Score: {result['ats_score']}/100")
            return result

        except Exception as e:
            print(f"Error in ATS checker: {e}")
            return {"ats_score": 0, "recommendation": "Error processing", "strong_point": "", "weak_point": ""}

    
    def per_dimension_score(self, resume_text: str, job_role: str) -> Dict[str, Any]:
        """
        Per Dimension Score Agent - Job matching evaluation
    
        Returns:
            Dictionary with skill_match, experience_match, role_match, certification_bonus, experience_label
        """

        system_message = f"""Evaluate the resume for the job role: {job_role}.
Return output strictly in JSON format only.

You must provide the following fields with scores between 0 and 1:
- skill_match
- experience_match
- role_match
- certification_bonus
- experience_label (set to \"fresher\" only if the candidate has zero work experience, otherwise \"experienced\")

IMPORTANT RULE (do not infer): Count experience ONLY from explicit work entries (company name/role + date range). 
If there are no explicit work entries, set experience_match = 0 and experience_label = \"fresher\".
Do NOT treat projects, coursework, publications, or skills as professional work experience.

Do NOT include any text outside the JSON.
"""

        prompt = f"{system_message}\n\nResume (first 2000 chars):\n{resume_text[:2000]}"

        try:
            response = self._call_gemini_with_retry(
                prompt=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,  # deterministic
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "skill_match": {"type": "number"},
                            "experience_match": {"type": "number"},
                            "role_match": {"type": "number"},
                            "certification_bonus": {"type": "number"},
                            "experience_label": {"type": "string"},
                        },
                        "required": ["skill_match", "experience_match", "role_match", "certification_bonus", "experience_label"],
                    },
                ),
            )
        
            
            text = getattr(response, "text", None) or getattr(response, "content", None) or str(response)
            parsed = self._safe_parse_text_to_json(text)
            if not parsed:
                raise ValueError("Could not parse per-dimension JSON")
        
            
            def to_clamped_float(val):
                try:
                    v = float(val)
                except Exception:
                    return 0.0
                return max(0.0, min(1.0, v))
        
            skill_match = to_clamped_float(parsed.get("skill_match", 0.0))
            experience_match = to_clamped_float(parsed.get("experience_match", 0.0))
            role_match = to_clamped_float(parsed.get("role_match", 0.0))
            certification_bonus = to_clamped_float(parsed.get("certification_bonus", 0.0))
            experience_label = parsed.get("experience_label", None)
            if not isinstance(experience_label, str) or experience_label.strip() == "":
                experience_label = "fresher" if experience_match == 0.0 else "experienced"
        
            
            if not self._has_work_experience(resume_text):
                experience_match = 0.0
                experience_label = "fresher"
        
            result = {
                "skill_match": skill_match,
                "experience_match": experience_match,
                "role_match": role_match,
                "certification_bonus": certification_bonus,
                "experience_label": experience_label,
            }
        
            print(f"✓ Per Dimension Score completed - Skill: {result['skill_match']:.2f}, Experience: {result['experience_match']:.2f}, Label: {result['experience_label']}")
            return result
        
        except Exception as e:
            print(f"Error in dimension scoring: {str(e)}")
            return {
                "skill_match": 0.0,
                "experience_match": 0.0,
                "role_match": 0.0,
                "certification_bonus": 0.0,
                "experience_label": "fresher",
            }

    def final_score(
        self,
        resume_text: str,
        ats_score: int,
        skill_match: float,
        experience_match: float,
        role_match: float,
        certification_bonus: float,
        experience_label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Final Score Agent - Calculate weighted final score and extract contact info

        Returns dictionary with:
          - name, email, phone_number
          - final_score (0-1)
          - experience_label
        """

        def clamp(v):
            try:
                v = float(v)
            except Exception:
                return 0.0
            return max(0.0, min(1.0, v))

        skill_match = clamp(skill_match)
        experience_match = clamp(experience_match)
        role_match = clamp(role_match)
        certification_bonus = clamp(certification_bonus)
        normalized_ats = clamp(ats_score / 100.0)

        calculated_score = (
            0.50 * skill_match
            + 0.20 * experience_match
            + 0.15 * role_match
            + 0.10 * normalized_ats
            + 0.05 * certification_bonus
        )
        final_score_value = round(clamp(calculated_score), 3)

        if experience_label is None:
            experience_label = "fresher" if experience_match == 0.0 else "experienced"

        
        system_message = """Extract contact information from resume.
Return JSON with name, email, and phone_number as strings.
If not found, return empty string for that field."""

        prompt = f"""{system_message}

Resume Text (first 1500 chars):
{resume_text[:1500]}"""

        try:
            response = self._call_gemini_with_retry(
                prompt=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string"},
                            "phone_number": {"type": "string"},
                        },
                        "required": ["name", "email", "phone_number"],
                    },
                ),
            )

            text = getattr(response, "text", None) or getattr(response, "content", None) or str(response)
            parsed = self._safe_parse_text_to_json(text) or {}

            result = {
                "name": parsed.get("name") or None,
                "email": parsed.get("email") or None,
                "phone_number": parsed.get("phone_number") or None,
                "final_score": final_score_value,
                "experience_label": experience_label,
            }

            print(f"✓ Final Score calculated: {final_score_value}")
            return result

        except Exception as e:
            print(f"⚠️ Contact extraction failed: {e}")
            return {
                "name": None,
                "email": None,
                "phone_number": None,
                "final_score": final_score_value,
                "experience_label": experience_label,
            }
    def _has_work_experience(self, text: str) -> bool:
        """
        Heuristic to detect explicit work experience entries in resume text.
        Returns True if there are likely job/company/date entries.
    
        Rules used:
        - Look for common section headings: 'experience', 'work experience', 'employment'
        - Look for date ranges e.g. 'Jan 2020 - Mar 2022', '2020 — 2022', or standalone years (2018, 2021)
        - Look for 'at <Company>' or 'Worked at' or 'Intern' (counts as experience)
        - If none found, consider the resume to have NO explicit work experience
        """
        if not text:
            return False
    
        t = text.lower()
    
        
        if re.search(r"\b(work|professional|employment|experience|experience:|work experience)\b", t):
            return True
    
        
        if re.search(r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s+\d{4}\s*[-–—]\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s+\d{4}", t):
            return True
        if re.search(r"\b(19|20)\d{2}\s*[-–—]\s*(19|20)\d{2}\b", t):
            return True
        
        if re.search(r"\b(19|20)\d{2}\b.*?[-–—to]{1,3}.*?\b(19|20)\d{2}\b", t):
            return True
        
        if re.search(r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s+\d{4}", t):
            return True
        
        if re.search(r"\b(worked at|worked as|at [A-Za-z0-9&\.\-]{2,})\b", t):
            return True
        if re.search(r"\bintern(ship)?\b", t):
            return True
    
        return False

    
    def process_application(
        self,
        pdf_path: str,
        job_role: str,
        candidate_name: str = None,
        candidate_email: str = None,
        candidate_linkedin: str = None,
    ) -> Dict[str, Any]:
        """
        Process a complete job application through the pipeline

        Returns the complete processing result. This version is defensive:
        - uses .get on dicts returned by agents
        - ensures `experience_label` is propagated
        - catches unexpected exceptions and returns a safe fallback
        """
        try:
            print(f"\n{'='*60}")
            print(f"Processing Application for: {job_role}")
            print(f"{'='*60}")

            print("\n[1/4] Extracting PDF text...")
            resume_text = self.extract_text_from_pdf(pdf_path)
            print(f"✓ Extracted {len(resume_text)} characters")

            print("\n[2/4] Running ATS Checker...")
            ats_result = self.ats_checker(resume_text, job_role) or {}
            ats_score = int(ats_result.get("ats_score", 0))

            meets_threshold = ats_score >= self.ats_threshold
            if not meets_threshold:
                print(f"\n⚠️  ATS Score ({ats_score}) below threshold ({self.ats_threshold})")
                print("    Continuing with full evaluation...")

            print("\n[3/4] Calculating Per Dimension Scores...")
            dimension_scores = self.per_dimension_score(resume_text, job_role) or {}
            skill_match = float(dimension_scores.get("skill_match", 0.0))
            experience_match = float(dimension_scores.get("experience_match", 0.0))
            role_match = float(dimension_scores.get("role_match", 0.0))
            certification_bonus = float(dimension_scores.get("certification_bonus", 0.0))
            experience_label = dimension_scores.get("experience_label", "fresher" if experience_match == 0.0 else "experienced")

            print("\n[4/4] Calculating Final Score...")
            final_result = self.final_score(
                resume_text,
                ats_score,
                skill_match,
                experience_match,
                role_match,
                certification_bonus,
                experience_label=experience_label,
            ) or {}

            status = "processed" if meets_threshold else "below_threshold"

            complete_result = {
                "status": status,
                "meets_ats_threshold": meets_threshold,
                "candidate_info": {
                    "name": final_result.get("name") or candidate_name,
                    "email": final_result.get("email") or candidate_email,
                    "phone": final_result.get("phone_number"),
                    "linkedin": candidate_linkedin,
                },
                "job_role": job_role,
                "ats_check": {
                    "score": ats_score,
                    "threshold": self.ats_threshold,
                    "recommendation": ats_result.get("recommendation", ""),
                    "strong_point": ats_result.get("strong_point", ""),
                    "weak_point": ats_result.get("weak_point", ""),
                },
                "dimension_scores": {
                    "skill_match": skill_match,
                    "experience_match": experience_match,
                    "role_match": role_match,
                    "certification_bonus": certification_bonus,
                    "experience_label": experience_label,
                },
                "final_score": final_result.get(
                    "final_score",
                    round(
                        (
                            0.55 * skill_match
                            + 0.25 * experience_match
                            + 0.15 * (ats_score / 100.0)
                            + 0.05 * certification_bonus
                        ),
                        3,
                    ),
                ),
            }

            print(f"\n{'='*60}")
            print("✅ Processing Complete!")
            print(f"{'='*60}")
            print(f"Status: {status.upper()}")
            print(f"Final Score: {complete_result['final_score']:.3f}")
            print(f"Candidate: {complete_result['candidate_info']['name']}")
            print(f"Email: {complete_result['candidate_info']['email']}")

            # Send email only if enabled via environment variable
            email_enabled = os.getenv("ENABLE_EMAIL", "false").lower() == "true"
            
            if email_enabled:
                try:
                    print("\n[5/5] Sending email notification...")
                    from email_service import EmailService
                    email_service = EmailService()
                    email_sent = email_service.send_application_result(complete_result)
                    complete_result["email_sent"] = email_sent
                except Exception as e:
                    print(f"⚠️ Email sending failed: {e}")
                    complete_result["email_sent"] = False
            else:
                print("\n⚠️ Email notifications disabled (set ENABLE_EMAIL=true to enable)")
                complete_result["email_sent"] = False

            return complete_result


        except Exception as e:
            
            print(f"❌ Error processing application: {e}")
            return {
                "status": "error",
                "meets_ats_threshold": False,
                "candidate_info": {"name": candidate_name, "email": candidate_email, "phone": None, "linkedin": candidate_linkedin},
                "job_role": job_role,
                "ats_check": {"score": 0, "threshold": self.ats_threshold, "recommendation": "", "strong_point": "", "weak_point": ""},
                "dimension_scores": {"skill_match": 0.0, "experience_match": 0.0, "role_match": 0.0, "certification_bonus": 0.0, "experience_label": "fresher"},
                "final_score": 0.0,
                "error": str(e),
            }
            
           
            


if __name__ == "__main__":
    
    pipeline = RecruitmentPipeline(ats_threshold=70)

    result = pipeline.process_application(
        pdf_path="sample_resume.pdf",  
        job_role="Machine Learning Engineer",
        candidate_name="John Doe",  
        candidate_email="john@example.com",  
        candidate_linkedin="linkedin.com/in/johndoe",  
    )
    output_file = "recruitment_result.json"
    with open(output_file, "w") as f:
        json.dump(result, indent=2, fp=f)

    print(f"\n📄 Results saved to: {output_file}")