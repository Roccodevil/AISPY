import os
import cv2
import time
import requests
import base64
import json
from groq import Groq

# Load Keys
HF_TOKEN = os.getenv("HUGGINGFACE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Active Deepfake Models on HF Free Tier
HF_DEEPFAKE_MODELS = [
    "prithivMLmods/deepfake-detector-model-v1",
    "dima806/deepfake_vs_real_image_detection"
]

def check_hf_deepfake(image_data):
    """Checks for deepfakes using Hugging Face's working models."""
    for model_id in HF_DEEPFAKE_MODELS:
        url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
        print(f"  ☁️ Sending to HF: {model_id}...")
        
        try:
            response = requests.post(url, headers=HF_HEADERS, data=image_data)
            
            if response.status_code == 200:
                scores = response.json()
                if isinstance(scores, list) and isinstance(scores[0], list): 
                    scores = scores[0]
                
                for item in scores:
                    label = item.get('label', '').lower()
                    if label in ['fake', 'artificial', 'deepfake', 'ai', 'generated']:
                        return item.get('score', 0.0), f"AI Detector Flagged: {item.get('label')} ({item.get('score'):.1%})"
                    elif label in ['real', 'human', 'realism']:
                        if item.get('score', 0.0) > 0.9:
                            return 0.0, f"Classified as Real/Authentic ({item.get('score'):.1%})"
                return 0.0, "Inconclusive"
                
            elif response.status_code == 503:
                print(f"  💤 HF Model Loading... waiting 3s")
                time.sleep(3)
                retry = requests.post(url, headers=HF_HEADERS, data=image_data)
                if retry.status_code == 200:
                    # Quick parse on retry
                    return retry.json()[0]['score'] if 'fake' in retry.json()[0]['label'].lower() else 0.0, "Checked on retry"
                    
        except Exception as e:
            print(f"  ❌ HF Connection Error: {e}")
            
    return 0.0, "All HF Models Failed"

def get_groq_context(image_path):
    """Uses Groq Vision for smart captioning and subject identification."""
    if not groq_client: return "Context unavailable (Groq Key Missing)"
    
    print(f"  👁️ Sending to Groq Vision for context...")
    try:
        with open(image_path, "rb") as image_file:
            b64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        prompt = """
        Describe this image in detail. What is happening? Who is in it?
        Return ONLY a JSON object: {"caption": "detailed description", "subject": "name or 'Unknown'"}
        """

        completion = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
                    ],
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        data = json.loads(completion.choices[0].message.content)
        return f"{data.get('caption', 'Image content')}. Subject: {data.get('subject', 'Unknown')}"
        
    except Exception as e:
        print(f"  ❌ Groq Vision Error: {e}")
        return "Context analysis failed."

def extract_frame(video_path):
    print("🎬 Extracting frame from video...")
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened(): return None
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
    print(f"👁️ Processing {media_type} via API...")
    analysis_image = media_path
    frame_extracted = False

    if media_type == "video":
        extracted = extract_frame(media_path)
        if extracted:
            analysis_image = extracted
            frame_extracted = True
        else:
            return {"visual_evidence": "Video Error", "generated_caption": "Error", "fake_probability": 0.0}

    try:
        with open(analysis_image, "rb") as f:
            image_data = f.read()
    except Exception as e:
        return {"visual_evidence": "Read Error", "generated_caption": str(e), "fake_probability": 0.0}

    # Step 1: Deepfake Detection (Hugging Face)
    fake_prob, evidence = check_hf_deepfake(image_data)

    # Step 2: Smart Context (Groq Vision)
    full_context = get_groq_context(analysis_image)
    
    print(f"📝 Final Context: {full_context}")

    if frame_extracted and os.path.exists(analysis_image):
        os.remove(analysis_image)

    return {
        "visual_evidence": evidence,
        "fake_probability": fake_prob,
        "generated_caption": full_context
    }