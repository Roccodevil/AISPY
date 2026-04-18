"""
Media Helper Utilities
OpenCV-based frame extraction from videos for temporal analysis
"""
import cv2
import os


def extract_frames(video_path, num_frames=3):
    """
    Extracts evenly spaced frames from a video for temporal analysis.
    Returns a list of file paths to the extracted images.
    """
    print(f"🎬 Extracting {num_frames} frames for temporal analysis...")
    extracted_paths = []
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("❌ Cannot open video file.")
            return []
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            return []

        # Calculate frame intervals (e.g., 25%, 50%, 75%)
        intervals = [int(total_frames * (i + 1) / (num_frames + 1)) for i in range(num_frames)]
        
        for idx, frame_pos in enumerate(intervals):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            if ret:
                frame_path = f"{video_path}_frame_{idx}.jpg"
                cv2.imwrite(frame_path, frame)
                extracted_paths.append(frame_path)
                
        cap.release()
        return extracted_paths
        
    except Exception as e:
        print(f"❌ Video extraction error: {e}")
        return []


def cleanup_files(file_paths):
    """Deletes temporary media files after analysis is complete."""
    if isinstance(file_paths, str):
        file_paths = [file_paths]
        
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"⚠️ Could not delete temporary file {path}: {e}")


def is_video_file(file_path: str) -> bool:
    """
    Check if a file is a video based on its extension.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file appears to be a video, False otherwise
    """
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v'}
    _, ext = os.path.splitext(file_path.lower())
    return ext in video_extensions


def is_image_file(file_path: str) -> bool:
    """
    Check if a file is an image based on its extension.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file appears to be an image, False otherwise
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    _, ext = os.path.splitext(file_path.lower())
    return ext in image_extensions
