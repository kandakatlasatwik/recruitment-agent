"""
Interactive recruitment pipeline - Choose job role
"""

from agent import RecruitmentPipeline
from pathlib import Path
import json

def main():
    """Run recruitment pipeline with user input"""
    
    pipeline = RecruitmentPipeline()
    
    # Display available job roles
    print("\n" + "="*60)
    print("🎯 RECRUITMENT PIPELINE - JOB ROLE SELECTION")
    print("="*60)
    print("\nAvailable Job Roles:")
    for idx, role in enumerate(pipeline.job_roles, 1):
        print(f"{idx}. {role}")
    
    # Get user selection
    while True:
        try:
            choice = input("\nSelect job role (1-4): ").strip()
            role_idx = int(choice) - 1
            if 0 <= role_idx < len(pipeline.job_roles):
                selected_role = pipeline.job_roles[role_idx]
                break
            else:
                print("❌ Invalid choice. Please enter 1-4.")
        except ValueError:
            print("❌ Please enter a number.")
    
    # Get PDF path
    while True:
        pdf_path = input("\nEnter PDF filename (or path): ").strip()
        if Path(pdf_path).exists():
            break
        else:
            print(f"❌ File not found: {pdf_path}")
            print("   Make sure the PDF is in the current directory.")
    
    # Optional: Get candidate info
    print("\nOptional candidate info (press Enter to skip):")
    candidate_name = input("Name: ").strip() or None
    candidate_email = input("Email: ").strip() or None
    candidate_linkedin = input("LinkedIn: ").strip() or None
    
    # Process application
    result = pipeline.process_application(
        pdf_path=pdf_path,
        job_role=selected_role,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        candidate_linkedin=candidate_linkedin
    )
    
    # Save results
    output_file = f"result_{Path(pdf_path).stem}_{selected_role.replace(' ', '_')}.json"
    with open(output_file, 'w') as f:
        json.dump(result, indent=2, fp=f)
    
    print(f"\n📄 Results saved to: {output_file}")
    
    # Ask to process another
    another = input("\nProcess another application? (y/n): ").strip().lower()
    if another == 'y':
        main()  # Recursive call

if __name__ == "__main__":
    main()
