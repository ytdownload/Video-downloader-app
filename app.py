# app.py
# Import necessary libraries
import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yt_dlp

# --- Configuration for Production (Render) ---
DOWNLOAD_DIRECTORY = os.environ.get('DOWNLOAD_DIR', 'downloads')

# --- Flask App Initialization ---
app = Flask(__name__)

# --- CORS Configuration ---
origins = ["https://ytdownload.github.io"]
CORS(app, origins=origins, supports_credentials=True)


# --- Server Setup ---
def setup_server():
    """Creates the download directory if it doesn't exist."""
    if not os.path.exists(DOWNLOAD_DIRECTORY):
        os.makedirs(DOWNLOAD_DIRECTORY)

setup_server()

# --- API Endpoints ---

@app.route('/')
def index():
    """A simple root endpoint to confirm the backend is running."""
    return "<h1>YouTube Downloader Backend is running with yt-dlp!</h1>"


@app.route('/api/video-info', methods=['POST', 'OPTIONS'])
def download_video():
    """
    Handles the video download request using yt-dlp with anti-bot-detection measures.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if request.method == 'POST':
        try:
            url = request.get_json().get('url')
            if not url:
                return jsonify({"error": "URL is required."}), 400
        except Exception:
            return jsonify({"error": "Invalid request format."}), 400

        try:
            print(f"Processing URL with yt-dlp: {url}")

            # --- THE FIX IS HERE ---
            # We are adding options to make our request look more like a browser
            # and to ignore some common server-side issues.
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'nocheckcertificate': True,
                # This pretends we are a real browser, which can bypass bot detection
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
                }
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                
                # Check if yt-dlp signaled an error for this video
                if info_dict is None:
                    raise Exception("yt-dlp failed to extract video information. The video may be unavailable.")

                video_title = info_dict.get('title', 'Unknown Title')
                thumbnail_url = info_dict.get('thumbnail', None)
                filename = ydl.prepare_filename(info_dict)
                base_filename = os.path.basename(filename)

                print(f"Downloading '{video_title}'...")
                # Perform the actual download
                ydl.download([url])
                print(f"SUCCESS: Downloaded '{base_filename}'")

            return jsonify({
                "message": "Download successful!",
                "filename": base_filename,
                "video_title": video_title,
                "thumbnail_url": thumbnail_url
            }), 200

        except Exception as e:
            print(f"ERROR processing video with yt-dlp: {e}")
            traceback.print_exc()
            # Return a more specific error message to the user
            error_message = str(e)
            if "Sign in to confirm" in error_message:
                return jsonify({"error": "This video is protected by YouTube's anti-bot measures and cannot be downloaded from a server."}), 500
            return jsonify({"error": "Failed to process this video. It may be private or have other restrictions."}), 500


@app.route('/downloads/<path:filename>')
def get_file(filename):
    """
    Serves the downloaded video file to the user.
    """
    try:
        return send_from_directory(DOWNLOAD_DIRECTORY, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found."}), 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    
