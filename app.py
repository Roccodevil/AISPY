import os
import json
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the Analysis Agents
# Note: We removed 'video_gen' as requested
from utils import downloader, search_agent, ai_forensics, brain, visual_search

app = Flask(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'mp4', 'mov', 'avi'}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 

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
    print("\n" + "="*50)
    print("🚀 STARTING FORENSIC ANALYSIS (INSIGHT MODE)")
    print("="*50)
    
    media_path = None
    media_type = "text"
    user_input_text = request.form.get('input', '').strip()
    text_claim = request.form.get('text_claim', '').strip() # NEW text claim input
    file_obj = request.files.get('file')

    # --- INPUT VALIDATION ---
    if not file_obj and not user_input_text and not text_claim:
        return jsonify({"error": "Please provide a media file, URL, or text claim."}), 400

    try:
        # --- STAGE 1: INGESTION (Download/Save) ---
        if file_obj:
            print("[DEBUG] Step 1: Processing File Upload...")
            if allowed_file(file_obj.filename):
                filename = secure_filename(file_obj.filename)
                media_path = os.path.join(downloader.DOWNLOAD_FOLDER, filename)
                file_obj.save(media_path)
                media_type = "video" if filename.lower().endswith(('.mp4', '.mov', '.avi')) else "image"
            else:
                return jsonify({"error": "Invalid file type"}), 400
        
        elif user_input_text and user_input_text.startswith("http"):
            print(f"[DEBUG] Step 1: Downloading from URL: {user_input_text}")
            path, detected_type = downloader.download_media(user_input_text)
            if path:
                media_path = path
                media_type = detected_type
            else:
                return jsonify({"error": "Could not download content from link."}), 400

        # --- STAGE 2: MULTI-MODEL FORENSICS & DEFAULTS ---
        # Default values for Text-Only Mode
        deepfake_data = "N/A - Text claim only. No visual media provided."
        search_query = text_claim or user_input_text
        fake_prob = 0.0
        ai_caption = ""
        
        if media_path:
            print(f"[DEBUG] Step 2: Running Ensemble Forensics on {media_path}...")
            try:
                results = ai_forensics.analyze_media(media_path, media_type)
                visual_data = results.get('visual_evidence', 'N/A')
                ai_caption = results.get('generated_caption', 'No caption')
                fake_prob = results.get('fake_probability', 0.0)
                
                deepfake_data = f"{visual_data} (Calculated Fake Probability: {fake_prob*100:.1f}%)"
                print(f"[DEBUG] Visual Evidence: {visual_data}")
                print(f"[DEBUG] AI Caption: {ai_caption}")
                
                # If user uploaded media but didn't type a claim, search using the AI caption
                if not text_claim and not user_input_text:
                    search_query = ai_caption if len(ai_caption) > 10 else "Unknown media context"
                    
            except Exception as e:
                print(f"❌ [DEBUG] Forensics Crashed: {e}")
                deepfake_data = "Forensics Analysis Failed"

        # --- STAGE 3: VISUAL SEARCH (Google Lens Clone) ---
        lens_results = []
        if user_input_text and user_input_text.startswith("http"):
             print(f"[DEBUG] Step 3: Running Visual Search (Lens) on URL...")
             lens_results = visual_search.google_lens_search(user_input_text)

        # --- STAGE 4: TEXT SEARCH (The Investigator) ---
        print(f"[DEBUG] Step 4: Searching Web for: '{search_query}'")
        search_result = search_agent.verify_claims(search_query)
        
        combined_sources = search_result.get('sources', []) + lens_results
        print(f"[DEBUG] Found {len(combined_sources)} total references.")

        # --- STAGE 5: BRAIN SYNTHESIS (The Verdict) ---
        print("[DEBUG] Step 5: Synthesizing Verdict...")
        
        raw_json_string = brain.generate_verdict(
            query=search_query,
            deepfake_data=deepfake_data,
            search_data=json.dumps(search_result)
        )
        
        # --- STAGE 6: PARSING ---
        try:
            final_data = json.loads(raw_json_string)
        except Exception:
            final_data = {
                "verdict": "Unverified",
                "confidence": 0,
                "reasoning": "AI analysis complete, but formatting failed."
            }

        # Inject data for the Explainable AI (XAI) Certificate
        final_data['context_sources'] = combined_sources
        final_data['extracted_context'] = ai_caption
        final_data['visual_evidence'] = deepfake_data

        # Cleanup
        if media_path:
            downloader.cleanup_file(media_path)

        return jsonify(final_data)

    except Exception as e:
        print(f"🔥 CRITICAL SYSTEM ERROR: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)