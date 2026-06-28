import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from pdf_reader import extract_text_from_pdf, PDFExtractionError
from summarizer import generate_summary

# Initialize Flask Application
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS) so the React frontend can make requests
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20 MB Upload Limit

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

@app.route('/', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "healthy",
        "message": "AI-Powered PDF Summarizer API is running."
    }), 200

@app.route('/upload', methods=['POST'])
def upload_pdf():
    """
    Endpoint to upload a PDF file and extract its text.
    Expects a multi-part form data request containing a file under the key 'file'.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only PDF documents are allowed."}), 400
        
    # Save the file securely
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(file_path)
        
        # Extract text using pdf_reader utility
        extraction_result = extract_text_from_pdf(file_path)
        
        # Add the filename to the response
        extraction_result["filename"] = filename
        
        return jsonify(extraction_result), 200
        
    except PDFExtractionError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error handling upload: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred during PDF processing: {str(e)}"}), 500
    finally:
        # Clean up the file after processing to save disk space
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                app.logger.warning(f"Failed to remove temporary file {file_path}: {e}")

@app.route('/summarize', methods=['POST'])
def summarize_text():
    """
    Endpoint to summarize extracted text.
    Expects a JSON body with keys:
    - text (str, required)
    - model_type (str, optional, default 'textrank')
    - length (str, optional, default 'medium')
    - api_key (str, optional)
    """
    data = request.get_json() or {}
    
    text = data.get('text', '').strip()
    model_type = data.get('model_type', 'textrank')
    length = data.get('length', 'medium')
    api_key = data.get('api_key', None)
    
    if not text:
        return jsonify({"error": "No text provided for summarization."}), 400
        
    try:
        summary_result = generate_summary(
            text=text,
            model_type=model_type,
            length=length,
            api_key=api_key
        )
        return jsonify(summary_result), 200
    except Exception as e:
        app.logger.error(f"Error generating summary: {str(e)}")
        return jsonify({"error": f"Failed to generate summary: {str(e)}"}), 500

# Error Handler for payload too large
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File size exceeds the maximum limit of 20 MB."}), 413

if __name__ == '__main__':
    # Running locally on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
