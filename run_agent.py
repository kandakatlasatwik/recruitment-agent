from agent import RecruitmentPipeline
from pathlib import Path
import json
import datetime
import sys

def sanitize_filename(s: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in s)

def choose_job_role(pipeline: RecruitmentPipeline) -> str:
    print("\n" + "="*60)
    print("🎯 RECRUITMENT PIPELINE ")
    print("="*60)
    print("\nAvailable Job Roles:")
    for idx, role in enumerate(pipeline.job_roles, 1):
        print(f"{idx}. {role}")

    while True:
        try:
            choice = input("\nSelect job role (number): ").strip()
            role_idx = int(choice) - 1
            if 0 <= role_idx < len(pipeline.job_roles):
                return pipeline.job_roles[role_idx]
            else:
                print("❌ Invalid choice. Please enter a valid number from the list.")
        except ValueError:
            print("❌ Please enter a number (e.g. 1).")

def ask_pdf_path() -> str:
    while True:
        pdf_path = input("\nEnter PDF filename (or path): ").strip()
        if Path(pdf_path).exists():
            return pdf_path
        else:
            print(f"❌ File not found: {pdf_path}")
            print("   Make sure the PDF is in the current directory or provide a full path.")

def run_once(pipeline: RecruitmentPipeline):
    try:
        selected_role = choose_job_role(pipeline)
        pdf_path = ask_pdf_path()

        candidate_name = None
        candidate_email = None
        candidate_linkedin = None

        print("\nProcessing... (Calling the AI agents...)\n")

        result = pipeline.process_application(
            pdf_path=pdf_path,
            job_role=selected_role,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            candidate_linkedin=candidate_linkedin
        )

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = Path(pdf_path).stem
        role_safe = sanitize_filename(selected_role.replace(" ", "_"))
        output_file = f"result_{stem}_{role_safe}_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Results saved to: {output_file}")

        print("\n--- SUMMARY ---")
        cand = result.get("candidate_info", {})
        print(f"Candidate name: {cand.get('name') or 'N/A'}")
        print(f"Candidate email: {cand.get('email') or 'N/A'}")
        print(f"Job role: {result.get('job_role')}")
        print(f"ATS score: {result.get('ats_check', {}).get('score', 'N/A')}")
        ats_check = result.get("ats_check", {})
        sp = ats_check.get("strong_point") or ats_check.get("strongPoint")
        wp = ats_check.get("weak_point") or ats_check.get("weakPoint")
        if sp:
            print(f"Strong point: {sp}")
        if wp:
            print(f"Weak point: {wp}")
        ds = result.get("dimension_scores", {})
        print(f"Experience label: {ds.get('experience_label', 'N/A')}")
        print(f"Final score: {result.get('final_score', 'N/A')}")
        print("----------------\n")

    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")

def main():
    """
    Entry point. Lets user process multiple applications in a loop.
    """
    print("Starting Recruitment Pipeline runner.\n")

    try:
        pipeline = RecruitmentPipeline()  
    except Exception as e:
        print(f"Failed to initialize pipeline: {e}")
        return

    while True:
        run_once(pipeline)
        again = input("Process another application? (y/n): ").strip().lower()
        if again != "y":
            print("Goodbye.")
            break

if __name__ == "__main__":
    main()