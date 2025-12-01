from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import json

# Import your existing RecruitmentPipeline
from agent import RecruitmentPipeline

load_dotenv()

app = Flask(__name__)
CORS(app, 
     resources={r"/api/*": {"origins": [
         "https://recruitment-agent-frontend.onrender.com",
         "http://localhost:5173",
         "http://localhost:5000"
     ]}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize pipeline
try:
    pipeline = RecruitmentPipeline(ats_threshold=70)
    print("✅ Pipeline initialized!")
except Exception as e:
    print(f"❌ Error: {e}")
    pipeline = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =============== API ENDPOINTS ===============

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Backend running',
        'pipeline_ready': pipeline is not None
    }), 200

@app.route('/api/job-roles', methods=['GET'])
def get_job_roles():
    if not pipeline:
        return jsonify({'error': 'Pipeline not ready'}), 500
    return jsonify({'roles': pipeline.job_roles}), 200

@app.route('/api/process', methods=['POST'])
def process_application():
    if not pipeline:
        return jsonify({'error': 'Pipeline not ready'}), 500
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file'}), 400
        
        file = request.files['file']
        job_role = request.form.get('job_role')
        
        if not job_role:
            return jsonify({'error': 'Job role required'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDFs allowed'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process with your agent
        result = pipeline.process_application(
            pdf_path=filepath,
            job_role=job_role,
            candidate_name=request.form.get('candidate_name'),
            candidate_email=request.form.get('candidate_email'),
            candidate_linkedin=request.form.get('candidate_linkedin')
        )
        
        # Cleanup
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#     print("\n" + "="*60)
#     print("🚀 Starting Recruitment Agent Backend")
#     print("="*60)
#     print("Backend: http://localhost:5000")
#     print("Frontend: http://localhost:5173")
#     print("="*60 + "\n")
#     app.run(debug=True, host='0.0.0.0', port=5000)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
