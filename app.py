# app.py
# Import necessary libraries
import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# We only need the core pytube components now
try:
    from pytube import YouTube
    from pytube.exceptions import PytubeError
    PYTUBE_AVAILABLE = True
except ImportError:
    PYTUBE_AVAILABLE = False

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
    pytube_status = "available" if PYTUBE_AVAILABLE else "NOT available"
    return f"<h1>YouTube Downloader Backend is running!</h1><p>Pytube library is {pytube_status}.</p>"


@app.route('/api/video-info', methods=['POST', 'OPTIONS'])
def download_video():
    """
    Handles the video download request, including the CORS OPTIONS preflight.
    This version removes the failing patch and relies on the base pytube library.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if request.method == 'POST':
        if not PYTUBE_AVAILABLE:
            return jsonify({"error": "Server configuration error: Video library is unavailable."}), 500

        try:
            url = request.get_json().get('url')
            if not url:
                return jsonify({"error": "URL is required."}), 400
        except Exception:
            return jsonify({"error": "Invalid request format."}), 400

        try:
            print(f"Processing URL: {url}")
            yt = YouTube(url)
            stream = yt.streams.get_highest_resolution()

            if not stream:
                return jsonify({"error": "No downloadable stream found for this video."}), 404

            print(f"Downloading '{yt.title}'...")
            stream.download(output_path=DOWNLOAD_DIRECTORY)
            filename = stream.default_filename
            print(f"SUCCESS: Downloaded '{filename}'")

            return jsonify({
                "message": "Download successful!",
                "filename": filename,
                "video_title": yt.title,
                "thumbnail_url": yt.thumbnail_url
            }), 200

        # This is the most likely error block to be triggered now.
        except PytubeError as e:
            print(f"PYTUBE ERROR: {e}")
            traceback.print_exc()
            # Provide a more helpful error message to the frontend
            return jsonify({"error": "The video library failed to process this specific video. It may be age-restricted, private, or a format the library cannot handle."}), 500
        
        except Exception as e:
            print(f"UNEXPECTED ERROR: {e}")
            traceback.print_exc()
            return jsonify({"error": "An unexpected server error occurred."}), 500


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
    
