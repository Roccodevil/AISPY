import os
import cv2
import numpy as np
from PIL import Image
from transformers import pipeline
from typing import Optional, Dict, List, Any

class EnsembleForensicsEngine:
    """
    Enterprise-grade forensics engine combining:
    - Face-specific deepfake detection (fine-tuned model)
    - Omni-scene manipulation detection (whole image analysis)
    - Temporal consistency checking (for videos)
    """
    
    def __init__(self, face_model_dir: str = None, omni_model_dir: str = None):
        """Initialize the dual-engine forensics system."""
        print("⚙️ Booting AI-SPY Ensemble Engine (CPU)...")
        
        # Define paths - handle spaces and special characters in directory names
        self.FACE_MODEL_DIR = face_model_dir or "./face_v2_enhanced (1)"
        self.OMNI_MODEL_DIR = omni_model_dir or "./omni_detector_v1"
        
        self.face_detector = None
        self.omni_detector = None
        self.face_tracker = None
        
        # Load models
        self._load_models()

    def _load_models(self):
        """Load both classification pipelines."""
        try:
            print(f"  📦 Loading Face Detection Model from {self.FACE_MODEL_DIR}...")
            self.face_detector = pipeline(
                "image-classification",
                model=self.FACE_MODEL_DIR,
                device=-1,  # CPU mode
                top_k=None,
                framework="pt"
            )
            print("  ✓ Face detector loaded successfully.")
        except Exception as e:
            print(f"  ⚠️ Face Model Load Error: {e}")
            self.face_detector = None

        try:
            print(f"  📦 Loading Omni Detection Model from {self.OMNI_MODEL_DIR}...")
            self.omni_detector = pipeline(
                "image-classification",
                model=self.OMNI_MODEL_DIR,
                device=-1,  # CPU mode
                top_k=None,
                framework="pt"
            )
            print("  ✓ Omni detector loaded successfully.")
        except Exception as e:
            print(f"  ⚠️ Omni Model Load Error: {e}")
            self.omni_detector = None

        # Load Haar Cascade for face tracking
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_tracker = cv2.CascadeClassifier(cascade_path)
            print("  ✓ Face tracker (Haar Cascade) loaded.")
        except Exception as e:
            print(f"  ⚠️ Face Tracker Load Error: {e}")
            self.face_tracker = None

    def extract_real_score(self, results: List[Dict[str, Any]]) -> float:
        """
        Extract the 'realness' score from model output.
        Handles various label formats from different model architectures.
        Returns: 0.0 to 100.0 (percentage confidence)
        """
        if not results:
            return 0.0
            
        scores = {res['label'].lower(): res['score'] for res in results}
        
        # Priority 1: Explicit "real" label
        if 'real' in scores:
            return scores['real'] * 100.0
        
        # Priority 2: Label indices (label_2 often means "real" in binary models)
        if 'label_2' in scores:
            return scores['label_2'] * 100.0
        if 'label_1' in scores:
            return scores['label_1'] * 100.0
        
        # Priority 3: Invert "fake" score
        if 'fake' in scores:
            return (1.0 - scores['fake']) * 100.0
        
        # Priority 4: Invert label_0 (often "fake" or "synthetic")
        if 'label_0' in scores:
            return (1.0 - scores['label_0']) * 100.0
        
        # Default: No clear real label found
        return 0.0

    def crop_face(self, cv_image: np.ndarray) -> Optional[Image.Image]:
        """
        Detect and crop the largest face from the image.
        Adds padding around the face for context.
        
        Args:
            cv_image: OpenCV image (BGR format)
        
        Returns:
            PIL Image of the cropped face, or None if no face detected
        """
        if self.face_tracker is None:
            return None
            
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        faces = self.face_tracker.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60)
        )
        
        if len(faces) == 0:
            return None
        
        # Use the largest face detected
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        x, y, w, h = faces[0]
        
        # Add padding (20% of face dimensions)
        ih, iw, _ = cv_image.shape
        mx, my = int(w * 0.2), int(h * 0.2)
        x1, y1 = max(0, x - mx), max(0, y - my)
        x2, y2 = min(iw, x + w + mx), min(ih, y + h + my)
        
        # Crop and convert to PIL
        crop = cv_image[y1:y2, x1:x2]
        if crop.size > 0:
            return Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
        
        return None

    def _analyze_image(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a single image file.
        
        Returns:
            Dict with metrics: scene_real_score, face_real_score
        """
        try:
            img_pil = Image.open(file_path).convert("RGB")
            cv_img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        except Exception as e:
            return {
                "scene_real_score": 0.0,
                "face_real_score": 0.0,
                "error": f"Failed to load image: {e}"
            }

        metrics = {}

        # Scene analysis
        if self.omni_detector:
            try:
                scene_results = self.omni_detector(img_pil)
                metrics["scene_real_score"] = self.extract_real_score(scene_results)
            except Exception as e:
                print(f"  ⚠️ Scene analysis failed: {e}")
                metrics["scene_real_score"] = 0.0
        else:
            metrics["scene_real_score"] = 0.0

        # Face analysis
        if self.face_detector:
            try:
                face_pil = self.crop_face(cv_img)
                if face_pil:
                    face_results = self.face_detector(face_pil)
                    metrics["face_real_score"] = self.extract_real_score(face_results)
                else:
                    metrics["face_real_score"] = 100.0  # No face found, assume authentic
            except Exception as e:
                print(f"  ⚠️ Face analysis failed: {e}")
                metrics["face_real_score"] = 0.0
        else:
            metrics["face_real_score"] = 0.0

        return metrics

    def _analyze_video(self, file_path: str, max_frames: int = 30) -> Dict[str, Any]:
        """
        Analyze a video by sampling frames at regular intervals.
        
        Args:
            file_path: Path to video file
            max_frames: Maximum number of frames to analyze
        
        Returns:
            Dict with metrics: avg_scene, min_scene, avg_face, min_face, frame_count
        """
        try:
            cap = cv2.VideoCapture(file_path)
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 300
            
            # Calculate frame skip to stay within max_frames limit
            frame_skip = max(1, total_frames // max_frames)
        except Exception as e:
            return {
                "avg_scene": 0.0,
                "min_scene": 0.0,
                "avg_face": 0.0,
                "min_face": 0.0,
                "error": f"Failed to open video: {e}"
            }

        scene_scores = []
        face_scores = []
        frame_count = 0
        analyzed_frames = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_skip == 0:
                analyzed_frames += 1
                
                # Scene analysis
                if self.omni_detector:
                    try:
                        pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        scene_results = self.omni_detector(pil_frame)
                        scene_score = self.extract_real_score(scene_results)
                        scene_scores.append(scene_score)
                    except Exception as e:
                        print(f"  ⚠️ Frame {frame_count} scene analysis failed: {e}")

                # Face analysis
                if self.face_detector:
                    try:
                        face_pil = self.crop_face(frame)
                        if face_pil:
                            face_results = self.face_detector(face_pil)
                            face_score = self.extract_real_score(face_results)
                            face_scores.append(face_score)
                    except Exception as e:
                        print(f"  ⚠️ Frame {frame_count} face analysis failed: {e}")

            frame_count += 1

        cap.release()

        # Calculate statistics
        metrics = {
            "avg_scene": sum(scene_scores) / len(scene_scores) if scene_scores else 100.0,
            "min_scene": min(scene_scores) if scene_scores else 100.0,
            "max_scene": max(scene_scores) if scene_scores else 100.0,
            "avg_face": sum(face_scores) / len(face_scores) if face_scores else 100.0,
            "min_face": min(face_scores) if face_scores else 100.0,
            "max_face": max(face_scores) if face_scores else 100.0,
            "frames_analyzed": analyzed_frames,
            "total_frames": total_frames
        }

        return metrics

    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        Main entry point: Analyze media and return structured forensic report.
        
        Args:
            file_path: Path to image or video file
        
        Returns:
            Structured dictionary with verdict and metrics
        """
        is_video = file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm'))
        
        report = {
            "type": "video" if is_video else "image",
            "is_fake": False,
            "confidence": 0.0,
            "reason": "",
            "metrics": {}
        }

        if not os.path.exists(file_path):
            report["reason"] = f"File not found: {file_path}"
            return report

        print(f"  🔍 Analyzing {'video' if is_video else 'image'}: {file_path}")

        # Analyze media
        if is_video:
            metrics = self._analyze_video(file_path)
        else:
            metrics = self._analyze_image(file_path)

        report["metrics"] = metrics

        # Determine verdict based on metrics
        if is_video:
            min_face = metrics.get("min_face", 100.0)
            min_scene = metrics.get("min_scene", 100.0)
            avg_face = metrics.get("avg_face", 100.0)
            avg_scene = metrics.get("avg_scene", 100.0)

            # Severe facial glitch detected
            if min_face < 40.0:
                report["is_fake"] = True
                report["confidence"] = 95.0
                report["reason"] = f"🚨 SEVERE FACIAL GLITCH | Frame dropped to {min_face:.1f}% authenticity"
            
            # Severe background anomaly
            elif min_scene < 40.0:
                report["is_fake"] = True
                report["confidence"] = 85.0
                report["reason"] = f"🚨 SEVERE BACKGROUND ANOMALY | Scene authenticity dropped to {min_scene:.1f}%"
            
            # Strict average threshold
            elif avg_face < 85.0 or avg_scene < 85.0:
                report["is_fake"] = True
                report["confidence"] = 80.0
                report["reason"] = f"⚠️ FAILED 85% THRESHOLD | Avg Face: {avg_face:.1f}%, Avg Scene: {avg_scene:.1f}%"
            
            # Likely authentic
            else:
                report["is_fake"] = False
                report["confidence"] = min(avg_face, avg_scene)  # Use lower score for confidence
                report["reason"] = f"✓ PASSED All Checks | Avg Face: {avg_face:.1f}%, Avg Scene: {avg_scene:.1f}%"
        
        else:  # Image analysis
            scene_score = metrics.get("scene_real_score", 0.0)
            face_score = metrics.get("face_real_score", 0.0)

            # Zero-tolerance check
            if scene_score < 80.0 or face_score < 80.0:
                report["is_fake"] = True
                report["confidence"] = 85.0
                report["reason"] = f"Failed Zero-Tolerance Check | Scene: {scene_score:.1f}%, Face: {face_score:.1f}%"
            else:
                report["is_fake"] = False
                report["confidence"] = min(scene_score, face_score)
                report["reason"] = f"Passed Authentication | Scene: {scene_score:.1f}%, Face: {face_score:.1f}%"

        return report
