from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import gc  # Garbage collector for memory management
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)

# CORS Configuration - Allow frontend to communicate
CORS(app, 
     resources={r"/api/*": {
         "origins": [
             "https://recruitment-agent-frontend.onrender.com",
             "http://localhost:5173",
             "http://localhost:5000"
         ],
         "methods": ["GET", "POST", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"],
         "supports_credentials": True
     }}
)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in [
        "https://recruitment-agent-frontend.onrender.com",
        "http://localhost:5173",
        "http://localhost:5000"
    ]:
        response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # Reduced to 5MB for memory safety

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Lazy load pipeline to save memory on startup
pipeline = None

def get_pipeline():
    """Initialize pipeline only when needed to save memory"""
    global pipeline
    if pipeline is None:
        try:
            from agent import RecruitmentPipeline
            pipeline = RecruitmentPipeline(ats_threshold=70)
            print("✅ Pipeline initialized!")
        except Exception as e:
            print(f"❌ Pipeline initialization error: {e}")
            raise
    return pipeline

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =============== API ENDPOINTS ===============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Backend running',
        'pipeline_ready': True
    }), 200

@app.route('/api/job-roles', methods=['GET'])
def get_job_roles():
    """Get available job roles"""
    try:
        pipe = get_pipeline()
        return jsonify({'roles': pipe.job_roles}), 200
    except Exception as e:
        print(f"❌ Error getting job roles: {e}")
        return jsonify({'error': 'Failed to load job roles'}), 500

@app.route('/api/process', methods=['POST', 'OPTIONS'])
def process_application():
    """Process resume application"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 204
    
    filepath = None
    
    try:
        # Validate file size
        if request.content_length and request.content_length > MAX_FILE_SIZE:
            return jsonify({'error': 'File too large (max 5MB)'}), 413
        
        # Validate file exists
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        job_role = request.form.get('job_role')
        
        # Validate inputs
        if not job_role:
            return jsonify({'error': 'Job role is required'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        print(f"📄 Processing resume: {filename} for role: {job_role}")
        
        # Get pipeline and process application
        pipe = get_pipeline()
        result = pipe.process_application(
            pdf_path=filepath,
            job_role=job_role,
            candidate_name=request.form.get('candidate_name'),
            candidate_email=request.form.get('candidate_email'),
            candidate_linkedin=request.form.get('candidate_linkedin')
        )
        
        print(f"✅ Processing completed successfully for {filename}")
        
        # Force garbage collection to free memory
        gc.collect()
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"❌ Error processing application: {e}")
        import traceback
        traceback.print_exc()
        
        error_message = str(e)
        if "rate limit" in error_message.lower():
            return jsonify({'error': 'API rate limit exceeded. Please try again later.'}), 429
        elif "memory" in error_message.lower():
            return jsonify({'error': 'Server memory error. Please try a smaller file.'}), 507
        else:
            return jsonify({'error': f'Processing failed: {error_message}'}), 500
    
    finally:
        # Always cleanup uploaded file
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"🗑️ Cleaned up file: {filepath}")
            except Exception as cleanup_error:
                print(f"⚠️ Failed to cleanup file: {cleanup_error}")
        
        # Force memory cleanup
        gc.collect()

# Error handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large (max 5MB)'}), 413

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

# Run application
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*60)
    print(f"🚀 Starting Recruitment Agent Backend on port {port}")
    print("="*60)
    app.run(host='0.0.0.0', port=port, threaded=False)
