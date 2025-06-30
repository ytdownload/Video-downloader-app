# app.py
# Import necessary libraries
import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# The new, more reliable downloader library
import yt_dlp

# --- Configuration for Production (Render) ---
DOWNLOAD_DIRECTORY = os.environ.get('DOWNLOAD_DIR', 'downloads')

# --- Flask App Initialization ---
app = Flask(__name__)

# --- CORS Configuration ---
# This is correct and allows your frontend to make requests.
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
    Handles the video download request using the yt-dlp library.
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

            # 1. Set up yt-dlp options
            # We specify the output path and filename format.
            # We also ask for the best quality mp4 video and audio.
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, '%(title)s.%(ext)s'),
            }

            # 2. Extract video info without downloading
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get('title', 'Unknown Title')
                thumbnail_url = info_dict.get('thumbnail', None)
                # Get the filename that yt-dlp *would* create
                filename = ydl.prepare_filename(info_dict)
                # We only want the basename, not the full path
                base_filename = os.path.basename(filename)

                print(f"Video Title: {video_title}")
                print(f"Filename: {base_filename}")

                # 3. Now, perform the actual download
                print(f"Downloading '{video_title}'...")
                ydl.download([url])
                print(f"SUCCESS: Downloaded '{base_filename}'")

            # 4. Return the info to the frontend
            return jsonify({
                "message": "Download successful!",
                "filename": base_filename,
                "video_title": video_title,
                "thumbnail_url": thumbnail_url
            }), 200

        except Exception as e:
            print(f"ERROR processing video with yt-dlp: {e}")
            traceback.print_exc()
            return jsonify({"error": "Failed to process this video with the new library. Please check the URL."}), 500


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
