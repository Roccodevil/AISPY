import os
import cv2
import subprocess
import pytesseract
from PIL import Image
from transformers import pipeline


class MediaIntelligenceAgent:
    def __init__(self):
        print("⚙️ Booting Sovereign Media Intelligence Agent (CPU)...")

        try:
            self.captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base", device=-1)
        except Exception as e:
            print(f"🚨 BLIP Load Error: {e}")
            self.captioner = None

        print("⚙️ Loading Hugging Face ASR (Wav2Vec2)...")
        try:
            self.transcriber = pipeline("automatic-speech-recognition", model="facebook/wav2vec2-base-960h", device=-1)
        except Exception as e:
            print(f"🚨 Transcriber Load Error: {e}")
            self.transcriber = None

        print("⚙️ Loading Hugging Face Audio Forensics...")
        try:
            self.audio_detector = pipeline("audio-classification", model="DunnBC22/wav2vec2-base-Fake_Real_Audio_Detection", device=-1)
        except Exception as e:
            print(f"🚨 Audio Forensics Load Error: {e}")
            self.audio_detector = None

    def extract_visuals(self, media_path):
        is_video = media_path.lower().endswith((".mp4", ".avi", ".mov"))
        captions, screen_text = [], set()

        if not is_video:
            try:
                pil_img = Image.open(media_path).convert("RGB")
                if self.captioner:
                    captions.append(self.captioner(pil_img, max_new_tokens=40)[0]["generated_text"])
                text = pytesseract.image_to_string(pil_img).strip()
                if len(text) > 4:
                    screen_text.add(" ".join(text.split()))
            except Exception:
                pass
        else:
            cap = cv2.VideoCapture(media_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            for t in [0.2, 0.5, 0.8]:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * t))
                ret, frame = cap.read()
                if ret:
                    pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    if self.captioner:
                        captions.append(self.captioner(pil_img, max_new_tokens=40)[0]["generated_text"].capitalize())
                    text = pytesseract.image_to_string(pil_img).strip()
                    if text and len(text) > 4:
                        screen_text.add(" ".join(text.split()))
            cap.release()

        visual_context = "### VISUAL SCENES ###\n" + "\n".join([f"- {c}" for c in captions])
        visual_context += "\n### ON-SCREEN TEXT ###\n" + ("\n".join([f"- {t}" for t in screen_text]) if screen_text else "- None")
        return visual_context

    def extract_audio(self, media_path):
        audio_path = "temp_audio.wav"
        result = {"transcript": "No audio detected.", "verdict": "N/A", "confidence": 0.0}

        subprocess.run(
            ["ffmpeg", "-i", media_path, "-ar", "16000", "-ac", "1", audio_path, "-y"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
            return result

        if self.transcriber:
            try:
                transcript_data = self.transcriber(audio_path)
                result["transcript"] = transcript_data["text"].strip()
            except Exception as e:
                print(f"  -> ⚠️ Transcription Error: {e}")

        if self.audio_detector:
            try:
                scores = self.audio_detector(audio_path)
                result["verdict"] = scores[0]["label"].upper()
                result["confidence"] = round(scores[0]["score"] * 100, 2)
            except Exception as e:
                print(f"  -> ⚠️ Voice Detection Error: {e}")

        if os.path.exists(audio_path):
            os.remove(audio_path)
        return result

    def analyze(self, media_path):
        print(f"  -> 🧠 Media Agent processing: {os.path.basename(media_path)}")
        return {
            "visual_context": self.extract_visuals(media_path),
            "audio_data": self.extract_audio(media_path),
        }
