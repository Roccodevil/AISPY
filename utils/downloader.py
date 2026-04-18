import os
import uuid
import yt_dlp

DOWNLOAD_FOLDER = 'temp_downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def download_media(url: str):
    """
    Downloads media from a given URL using yt-dlp.
    Returns the local file path and the media type ('video' or 'image').
    """
    try:
        # Generate a unique filename using UUID
        unique_id = str(uuid.uuid4())[:8]
        output_template = os.path.join(DOWNLOAD_FOLDER, f'{unique_id}.%(ext)s')

        ydl_opts = {
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'format': 'best[ext=mp4]/best', # Prioritize mp4 for OpenCV compatibility
        }

        print(f"  ⬇️ Attempting Download via yt-dlp: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            
            # Locate the downloaded file path
            ext = info_dict.get('ext', 'mp4')
            downloaded_file = os.path.join(DOWNLOAD_FOLDER, f'{unique_id}.{ext}')
            
            if os.path.exists(downloaded_file):
                print(f"  ✅ Downloaded: {downloaded_file}")
                # Determine type
                media_type = "video" if ext.lower() in ['mp4', 'webm', 'mkv', 'mov'] else "image"
                return downloaded_file, media_type
            else:
                print("  ❌ File download failed or could not be located.")
                return None, None

    except Exception as e:
        print(f"  ❌ yt-dlp Error: {e}")
        return None, None

def cleanup_file(filepath: str):
    """Removes the file after analysis to save space."""
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"⚠️ Could not delete {filepath}: {e}")

    return None, None

def cleanup_file(file_path):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except: pass