import os
import uuid
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our new architecture
from core.workflow import run_aispy_pipeline
from core.observability import init_langsmith_observability
from utils import downloader

app = Flask(__name__)
init_langsmith_observability()

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'mp4', 'mov', 'avi'}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50 MB limit

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # 1. Grab inputs from frontend
    file_obj = request.files.get('file')
    user_input_url = request.form.get('input', '').strip()
    text_claim = request.form.get('text_claim', '').strip()

    # Input Validation
    if not file_obj and not user_input_url and not text_claim:
        return jsonify({"error": "Please provide a media file, URL, or text claim."}), 400

    media_path = None
    input_type = "text" # Default to text
    request_id = str(uuid.uuid4())

    try:
        # 2. Ingest Media (If Provided)
        if file_obj and file_obj.filename != '':
            print("[SERVER] Processing local file upload...")
            if allowed_file(file_obj.filename):
                filename = secure_filename(file_obj.filename)
                media_path = os.path.join(downloader.DOWNLOAD_FOLDER, filename)
                file_obj.save(media_path)
                input_type = "media"
            else:
                return jsonify({"error": "Invalid file type."}), 400

        elif user_input_url and user_input_url.startswith("http"):
            print(f"[SERVER] Downloading from URL: {user_input_url}")
            media_path, _ = downloader.download_media(user_input_url)
            if not media_path:
                return jsonify({"error": "Could not download content from link."}), 400
            input_type = "media"

        # 3. Trigger the LangGraph Multi-Agent Workflow
        # This one line orchestrates the CNN, the Web Search, and the AI Agents!
        final_state = run_aispy_pipeline(
            input_type=input_type,
            media_path=media_path,
            text_claim=text_claim if text_claim else None,
            request_id=request_id
        )

        # 4. Handle Pipeline Errors
        if final_state.get("errors"):
            print(f"⚠️ Pipeline Errors: {final_state['errors']}")
            if not final_state.get("final_result"):
                return jsonify({"error": "Analysis failed: " + " | ".join(final_state["errors"])}), 500

        # 5. Extract Pydantic Objects for the XAI Frontend
        verdict_data = final_state.get("final_result")
        forensics_data = final_state.get("forensics_data")
        osint_data = final_state.get("osint_data")

        if not verdict_data:
             return jsonify({"error": "The AI Auditor failed to generate a verdict."}), 500

        # Map the strict Pydantic models to the JSON format expected by report.js
        response_data = {
            "verdict": verdict_data.verdict,
            "confidence": verdict_data.confidence,
            "reasoning": f"{verdict_data.reasoning} {verdict_data.xai_breakdown}",
            "final_report": final_state.get("final_report", ""),
            
            # XAI Details from Forensics
            "extracted_context": final_state.get("media_context", "") or (forensics_data.extracted_caption if forensics_data else "No vision context."),
            "visual_evidence": forensics_data.visual_evidence if forensics_data else "No visual forensics run.",
            
            # XAI Details from OSINT
            "context_sources": [{"url": url, "title": "Verified Source"} for url in osint_data.sources_used] if osint_data and osint_data.sources_used else []
        }

        # 6. Cleanup local files
        if media_path:
            downloader.cleanup_file(media_path)

        return jsonify(response_data)

    except Exception as e:
        print(f"🔥 CRITICAL SYSTEM ERROR: {e}")
        # Ensure cleanup happens even on crash
        if media_path:
             downloader.cleanup_file(media_path)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Start the Flask Server
    app.run(debug=True, port=5000)