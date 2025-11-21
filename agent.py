"""
Recruitment Pipeline Agent - Fixed Version
Converts n8n workflow to Python using Google ADK
"""

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

# Load environment variables
load_dotenv()


class RecruitmentPipeline:
    """Main recruitment pipeline with ATS scoring, job matching, and final scoring"""
    
    def __init__(self, ats_threshold: int = 70):
        """
        Initialize the pipeline with Gemini client
        
        Args:
            ats_threshold: Minimum ATS score to continue (default 70)
        """
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash"  # ✅ Fixed: Changed to stable model
        self.ats_threshold = ats_threshold
        
        # Job roles from the form
        self.job_roles = [
            "Machine Learning Engineer",
            "Agentic AI Engineer",
            "Software Developer",
            "Data Engineer"
        ]
        
        print(f"✅ Pipeline initialized")
        print(f"✅ ATS Threshold: {self.ats_threshold}/100\n")
    
    def _call_gemini_with_retry(self, prompt: str, config: types.GenerateContentConfig, max_retries: int = 3):
        """
        Call Gemini API with automatic retry on rate limit errors
        
        Args:
            prompt: The prompt to send
            config: Generation config
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response from Gemini API
        """
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                return response
                
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    # Extract retry delay from error message
                    match = re.search(r'retry in ([\d.]+)s', error_str)
                    if match:
                        wait_time = float(match.group(1))
                    else:
                        wait_time = 60  # Default wait time
                    
                    if attempt < max_retries - 1:
                        print(f"⏳ Rate limit hit. Waiting {wait_time:.1f} seconds before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time + 1)  # Add 1 second buffer
                        continue
                    else:
                        print(f"❌ Max retries reached. Error: {error_str}")
                        raise
                else:
                    # Not a rate limit error, raise immediately
                    raise
        
        raise Exception("Failed after all retries")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF resume
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting PDF: {str(e)}")
    
    def ats_checker(self, resume_text: str, job_role: str) -> Dict[str, Any]:
        """
        ATS Checker Agent - Analyzes resume compatibility
        
        Args:
            resume_text: Extracted resume text
            job_role: Selected job role
            
        Returns:
            Dictionary with ats_score and Recommendation
        """
        system_message = f"""Analyze resume for {job_role}. Return JSON only.
Score 1-100 for ATS compatibility. Provide brief recommendation (max 50 words)."""

        prompt = f"{system_message}\n\nResume:\n{resume_text[:3000]}"  # Limit to reduce tokens
        
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
                            "Recommendation": {"type": "string"}
                        },
                        "required": ["ats_score", "Recommendation"]
                    }
                )
            )
            
            result = json.loads(response.text)
            print(f"✓ ATS Checker completed - Score: {result['ats_score']}/100")
            return result
            
        except Exception as e:
            print(f"Error in ATS checker: {str(e)}")
            return {"ats_score": 0, "Recommendation": "Error processing"}
    
    def per_dimension_score(self, resume_text: str, job_role: str) -> Dict[str, float]:
        """
        Per Dimension Score Agent - Job matching evaluation
        
        Args:
            resume_text: Extracted resume text
            job_role: Selected job role
            
        Returns:
            Dictionary with skill_match, experience_match, role_match, certification_bonus
        """
        system_message = f"""Evaluate resume for {job_role}. Return JSON with scores 0-1:
skill_match, experience_match, role_match, certification_bonus

Score conservatively based on actual resume content."""

        prompt = f"{system_message}\n\nResume (first 2000 chars):\n{resume_text[:2000]}"
        
        try:
            response = self._call_gemini_with_retry(
                prompt=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "skill_match": {"type": "number"},
                            "experience_match": {"type": "number"},
                            "role_match": {"type": "number"},
                            "certification_bonus": {"type": "number"}
                        },
                        "required": ["skill_match", "experience_match", "role_match", "certification_bonus"]
                    }
                )
            )
            
            result = json.loads(response.text)
            print(f"✓ Per Dimension Score completed - Skill: {result['skill_match']:.2f}")
            return result
            
        except Exception as e:
            print(f"Error in dimension scoring: {str(e)}")
            return {
                "skill_match": 0.0,
                "experience_match": 0.0,
                "role_match": 0.0,
                "certification_bonus": 0.0
            }
    
    def final_score(
        self,
        resume_text: str,
        ats_score: int,
        skill_match: float,
        experience_match: float,
        role_match: float,
        certification_bonus: float
    ) -> Dict[str, Any]:
        """
        Final Score Agent - Calculate weighted final score and extract contact info
        
        Args:
            resume_text: Extracted resume text
            ats_score: ATS score from previous agent
            skill_match, experience_match, role_match, certification_bonus: Dimension scores
            
        Returns:
            Dictionary with name, email, phone_number, final_score
        """
        # ✅ ALWAYS calculate final score first
        normalized_ats = ats_score / 100.0
        calculated_score = (
            0.55 * skill_match +
            0.25 * experience_match +
            0.15 * normalized_ats +
            0.05 * certification_bonus
        )
        
        # Extract contact info
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
                            "name": {"type": "string"},  # ✅ Fixed: removed ["string", "null"]
                            "email": {"type": "string"},
                            "phone_number": {"type": "string"}
                        },
                        "required": ["name", "email", "phone_number"]
                    }
                )
            )
            
            contact_info = json.loads(response.text)
            
            # Convert empty strings to None
            result = {
                "name": contact_info.get("name") if contact_info.get("name") else None,
                "email": contact_info.get("email") if contact_info.get("email") else None,
                "phone_number": contact_info.get("phone_number") if contact_info.get("phone_number") else None,
                "final_score": round(calculated_score, 3)
            }
            
            print(f"✓ Final Score calculated: {result['final_score']:.3f}")
            return result
            
        except Exception as e:
            print(f"⚠️ Contact extraction failed: {str(e)}")
            # Still return calculated score
            return {
                "name": None,
                "email": None,
                "phone_number": None,
                "final_score": round(calculated_score, 3)
            }
    
    def process_application(
        self,
        pdf_path: str,
        job_role: str,
        candidate_name: str = None,
        candidate_email: str = None,
        candidate_linkedin: str = None
    ) -> Dict[str, Any]:
        """
        Process a complete job application through the pipeline
        
        Args:
            pdf_path: Path to the resume PDF
            job_role: Selected job role
            candidate_name: Optional - candidate name from form
            candidate_email: Optional - candidate email from form
            candidate_linkedin: Optional - LinkedIn profile
            
        Returns:
            Complete processing results
        """
        print(f"\n{'='*60}")
        print(f"Processing Application for: {job_role}")
        print(f"{'='*60}")
        
        # Step 1: Extract PDF text
        print("\n[1/4] Extracting PDF text...")
        resume_text = self.extract_text_from_pdf(pdf_path)
        print(f"✓ Extracted {len(resume_text)} characters")
        
        # Step 2: ATS Checker
        print("\n[2/4] Running ATS Checker...")
        ats_result = self.ats_checker(resume_text, job_role)
        
        # Step 3: Check ATS threshold (but continue anyway)
        meets_threshold = ats_result['ats_score'] > self.ats_threshold
        
        if not meets_threshold:
            print(f"\n⚠️  ATS Score ({ats_result['ats_score']}) below threshold ({self.ats_threshold})")
            print("    Continuing with full evaluation...")
        
        # Step 4: Per Dimension Score (always execute)
        print("\n[3/4] Calculating Per Dimension Scores...")
        dimension_scores = self.per_dimension_score(resume_text, job_role)
        
        # Step 5: Final Score (always execute)
        print("\n[4/4] Calculating Final Score...")
        final_result = self.final_score(
            resume_text,
            ats_result['ats_score'],
            dimension_scores['skill_match'],
            dimension_scores['experience_match'],
            dimension_scores['role_match'],
            dimension_scores['certification_bonus']
        )
        
        # Compile complete results
        status = "processed" if meets_threshold else "below_threshold"
        
        complete_result = {
            "status": status,
            "meets_ats_threshold": meets_threshold,
            "candidate_info": {
                "name": final_result.get('name') or candidate_name,
                "email": final_result.get('email') or candidate_email,
                "phone": final_result.get('phone_number'),
                "linkedin": candidate_linkedin
            },
            "job_role": job_role,
            "ats_check": {
                "score": ats_result['ats_score'],
                "threshold": self.ats_threshold,
                "recommendation": ats_result['Recommendation']
            },
            "dimension_scores": dimension_scores,
            "final_score": final_result['final_score']
        }
        
        print(f"\n{'='*60}")
        print("✅ Processing Complete!")
        print(f"{'='*60}")
        print(f"Status: {status.upper()}")
        print(f"Final Score: {final_result['final_score']:.3f}")
        print(f"Candidate: {complete_result['candidate_info']['name']}")
        print(f"Email: {complete_result['candidate_info']['email']}")
        
        return complete_result


# Main execution
if __name__ == "__main__":
    # Initialize pipeline with threshold
    pipeline = RecruitmentPipeline(ats_threshold=70)
    
    # Example usage
    result = pipeline.process_application(
        pdf_path="sample_resume.pdf",  # Replace with your PDF path
        job_role="Machine Learning Engineer",
        candidate_name="John Doe",  # Optional
        candidate_email="john@example.com",  # Optional
        candidate_linkedin="linkedin.com/in/johndoe"  # Optional
    )
    
    # Save results to JSON
    output_file = "recruitment_result.json"
    with open(output_file, 'w') as f:
        json.dump(result, indent=2, fp=f)
    
    print(f"\n📄 Results saved to: {output_file}")
