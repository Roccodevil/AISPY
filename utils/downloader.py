import os
import glob
import yt_dlp
import uuid
import requests
import shutil

DOWNLOAD_FOLDER = "temp_downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def download_media(url):
    print(f"⬇️ Attempting Download: {url}")
    unique_id = str(uuid.uuid4())[:8]
    
    # Check if direct image link
    if any(url.lower().endswith(ext) for ext in ['.jpg', '.png', '.webp']):
        try:
            # (Image download logic same as before...)
            return "path_to_image", "image"
        except: pass

    # Robust Video Download
    output_template = f"{DOWNLOAD_FOLDER}/{unique_id}.%(ext)s"
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best', # Force MP4
        'outtmpl': output_template,
        'geo_bypass': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        # This helps with YouTube Shorts
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find the file
        list_of_files = glob.glob(f"{DOWNLOAD_FOLDER}/{unique_id}*")
        if list_of_files:
            final_file = max(list_of_files, key=os.path.getsize)
            print(f"✅ Downloaded: {final_file}")
            return final_file, "video"
            
    except Exception as e:
        print(f"❌ Download Error: {e}")

    return None, None

def cleanup_file(file_path):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except: pass