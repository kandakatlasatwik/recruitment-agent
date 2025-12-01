import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class EmailService:
    """Email service for sending recruitment notifications"""

    def __init__(self):
        """Initialize email service with SMTP credentials from environment"""
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.company_name = os.getenv("COMPANY_NAME", "Our Company")

        if not self.sender_email or not self.sender_password:
            raise ValueError("SENDER_EMAIL and SENDER_PASSWORD must be set in environment variables")

        print(f"✅ Email Service initialized - Sender: {self.sender_email}")

    def send_selection_email(
        self,
        candidate_email: str,
        candidate_name: str,
        job_role: str,
        final_score: float,
        strong_points: str,
        next_steps: str = "Our HR team will contact you within 3-5 business days."
    ) -> bool:
        """
        Send selection notification email to candidate

        Args:
            candidate_email: Candidate's email address
            candidate_name: Candidate's name
            job_role: Applied job role
            final_score: Final evaluation score
            strong_points: Key strengths identified
            next_steps: Information about next steps

        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"Congratulations! Application Update for {job_role}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #28a745;">Congratulations, {candidate_name}! 🎉</h2>
                
                <p>We are pleased to inform you that your application for the position of <strong>{job_role}</strong> at {self.company_name} has been <strong>selected</strong> for the next round.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #28a745;">Evaluation Summary</h3>
                    <p><strong>Final Score:</strong> {final_score:.2%}</p>
                    <p><strong>Key Strengths:</strong></p>
                    <p>{strong_points}</p>
                </div>
                
                <h3>Next Steps</h3>
                <p>{next_steps}</p>
                
                <p>We look forward to connecting with you soon!</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="font-size: 12px; color: #666;">
                    Best regards,<br>
                    <strong>{self.company_name} Recruitment Team</strong>
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(candidate_email, subject, html_body)

    def send_rejection_email(
        self,
        candidate_email: str,
        candidate_name: str,
        job_role: str,
        final_score: float,
        weak_points: str,
        ats_score: int,
        recommendation: str
    ) -> bool:
        """
        Send rejection notification email to candidate

        Args:
            candidate_email: Candidate's email address
            candidate_name: Candidate's name
            job_role: Applied job role
            final_score: Final evaluation score
            weak_points: Areas for improvement
            ats_score: ATS score received
            recommendation: Feedback/recommendation

        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"Application Update for {job_role} at {self.company_name}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #dc3545;">Application Update</h2>
                
                <p>Dear {candidate_name},</p>
                
                <p>Thank you for your interest in the <strong>{job_role}</strong> position at {self.company_name} and for taking the time to apply.</p>
                
                <p>After careful consideration of your application, we regret to inform you that we will not be moving forward with your candidacy at this time.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #856404;">Evaluation Feedback</h3>
                    <p><strong>ATS Score:</strong> {ats_score}/100</p>
                    <p><strong>Final Score:</strong> {final_score:.2%}</p>
                    <p><strong>Areas for Improvement:</strong></p>
                    <p>{weak_points}</p>
                    <p><strong>Recommendation:</strong></p>
                    <p>{recommendation}</p>
                </div>
                
                <p>We encourage you to continue developing your skills and applying for future opportunities with us. We will keep your resume on file for consideration in other suitable positions.</p>
                
                <p>We appreciate your interest in {self.company_name} and wish you the best in your job search.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="font-size: 12px; color: #666;">
                    Best regards,<br>
                    <strong>{self.company_name} Recruitment Team</strong>
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(candidate_email, subject, html_body)

    def _send_email(self, recipient_email: str, subject: str, html_body: str) -> bool:
        """
        Internal method to send email via SMTP

        Args:
            recipient_email: Recipient's email address
            subject: Email subject
            html_body: HTML content of email

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = subject

            # Attach HTML content
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)

            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Secure connection
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            print(f"✅ Email sent successfully to {recipient_email}")
            return True

        except Exception as e:
            print(f"❌ Failed to send email to {recipient_email}: {str(e)}")
            return False

    def send_application_result(self, result: Dict[str, Any]) -> bool:
        """
        Send appropriate email based on application result

        Args:
            result: Complete application processing result from RecruitmentPipeline

        Returns:
            True if email sent successfully, False otherwise
        """
        candidate_info = result.get("candidate_info", {})
        candidate_email = candidate_info.get("email")
        candidate_name = candidate_info.get("name", "Candidate")

        if not candidate_email:
            print("⚠️ No candidate email found, skipping email notification")
            return False

        job_role = result.get("job_role", "the position")
        final_score = result.get("final_score", 0.0)
        ats_check = result.get("ats_check", {})
        
        # Determine selection criteria (you can adjust these thresholds)
        is_selected = final_score >= 0.50 and ats_check.get("score", 0) >= 50

        if is_selected:
            return self.send_selection_email(
                candidate_email=candidate_email,
                candidate_name=candidate_name,
                job_role=job_role,
                final_score=final_score,
                strong_points=ats_check.get("strong_point", "Your profile matches our requirements well."),
            )
        else:
            return self.send_rejection_email(
                candidate_email=candidate_email,
                candidate_name=candidate_name,
                job_role=job_role,
                final_score=final_score,
                weak_points=ats_check.get("weak_point", "We found other candidates who better match our current requirements."),
                ats_score=ats_check.get("score", 0),
                recommendation=ats_check.get("recommendation", "Consider strengthening your skills and experience in this domain."),
            )
