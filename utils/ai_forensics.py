import os
import cv2
import time
import requests
import base64
import json

# Load API Key
HF_TOKEN = os.getenv("HUGGINGFACE_API_KEY")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- 2025 WORKING MODEL REGISTRY ---
MODELS = {
    "deepfake": [
        # NEWEST & MOST ACTIVE (Feb 2025)
        "https://api-inference.huggingface.co/models/prithivMLmods/AI-vs-Deepfake-vs-Real-v2.0",
        "https://api-inference.huggingface.co/models/prithivMLmods/Deep-Fake-Detector-v2-Model",
        # FALLBACKS
        "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector",
        "https://api-inference.huggingface.co/models/not-ai-tech/content-autenticity-detection"
    ],
    "caption": [
        # Standard Stable Models
        "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large",
        "https://api-inference.huggingface.co/models/nlpconnect/vit-gpt2-image-captioning",
        "https://api-inference.huggingface.co/models/microsoft/git-base-coco"
    ],
    "vqa": [
        # Visual Question Answering
        "https://api-inference.huggingface.co/models/dandelin/vilt-b32-finetuned-vqa",
        "https://api-inference.huggingface.co/models/Salesforce/blip-vqa-base"
    ]
}

def query_with_fallback(task_name, payload):
    """
    Tries multiple models for a task until one works.
    """
    model_list = MODELS.get(task_name, [])
    
    for url in model_list:
        model_name = url.split('/')[-1]
        print(f"🔄 Trying {task_name} model: {model_name}...")
        try:
            # Send Request
            if isinstance(payload, dict):
                response = requests.post(url, headers=HEADERS, json=payload)
            else:
                response = requests.post(url, headers=HEADERS, data=payload)
            
            # Case: Success
            if response.status_code == 200:
                return response.json()
            
            # Case: Loading (Wait and Retry)
            elif response.status_code == 503:
                wait = response.json().get('estimated_time', 3)
                print(f"💤 Loading... waiting {wait:.1f}s")
                time.sleep(min(wait, 5))
                # Retry once
                if isinstance(payload, dict):
                    retry = requests.post(url, headers=HEADERS, json=payload)
                else:
                    retry = requests.post(url, headers=HEADERS, data=payload)
                if retry.status_code == 200:
                    return retry.json()

            # Case: Error
            print(f"⚠️ Failed ({response.status_code}). Switching to backup...")
            
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            
    print(f"❌ All models for {task_name} failed.")
    return None

def extract_frame(video_path):
    print("🎬 Extracting frame from video...")
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened(): return None
        # Get frame at 20% mark
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(cap.get(cv2.CAP_PROP_FRAME_COUNT) * 0.2))
        ret, frame = cap.read()
        cap.release()
        if ret:
            frame_path = video_path + "_frame.jpg"
            cv2.imwrite(frame_path, frame)
            return frame_path
    except: return None
    return None

def analyze_media(media_path, media_type):
    print(f"👁️ Processing {media_type}: {media_path}")
    analysis_image = media_path
    frame_extracted = False

    if media_type == "video":
        extracted = extract_frame(media_path)
        if extracted:
            analysis_image = extracted
            frame_extracted = True
        else:
            return {"visual_evidence": "Video Error", "generated_caption": "Video Error", "fake_probability": 0.0}

    try:
        with open(analysis_image, "rb") as f:
            image_data = f.read()
    except Exception as e:
        return {"visual_evidence": "Read Error", "generated_caption": str(e), "fake_probability": 0.0}

    # --- 1. FORENSICS (Real vs Fake) ---
    fake_prob = 0.0
    evidence = "Inconclusive"
    
    res_forensics = query_with_fallback("deepfake", image_data)
    
    if res_forensics:
        # Handle List vs Dict
        scores = res_forensics if isinstance(res_forensics, list) else [res_forensics]
        if isinstance(scores[0], list): scores = scores[0] 
        
        # Look for "Fake" labels
        for item in scores:
            label = item.get('label', '').lower()
            if label in ['fake', 'artificial', 'deepfake', 'ai', 'generated']:
                fake_prob = item.get('score', 0.0)
                evidence = f"AI Detection Model ({item.get('label')}) flagged this: {fake_prob:.0%}"
                break
            elif label in ['real', 'human']:
                real_score = item.get('score', 0.0)
                if real_score > 0.9:
                    evidence = f"Classified as Real/Human ({real_score:.0%})"

    # --- 2. CAPTIONING (Context) ---
    caption_text = "Image content"
    res_caption = query_with_fallback("caption", image_data)
    
    if res_caption:
        if isinstance(res_caption, list) and len(res_caption) > 0:
            caption_text = res_caption[0].get('generated_text', 'Image')
        elif isinstance(res_caption, dict):
            caption_text = res_caption.get('generated_text', 'Image')

    # --- 3. VQA (Specific Details) ---
    vqa_detail = ""
    # Only try VQA if we have a valid image
    b64_image = base64.b64encode(image_data).decode('utf-8')
    vqa_payload = {"inputs": {"image": b64_image, "question": "Who is in the image?"}}
    
    res_vqa = query_with_fallback("vqa", vqa_payload)
    if res_vqa and isinstance(res_vqa, list) and len(res_vqa) > 0:
        answer = res_vqa[0].get('answer')
        if answer and answer not in ['man', 'woman', 'person']:
            vqa_detail = f"Subject: {answer}"

    # Final Context String
    full_context = f"{caption_text}. {vqa_detail}".strip()
    print(f"📝 Final Context: {full_context}")

    # Cleanup
    if frame_extracted and os.path.exists(analysis_image):
        os.remove(analysis_image)

    return {
        "visual_evidence": evidence,
        "fake_probability": fake_prob,
        "generated_caption": full_context
    }