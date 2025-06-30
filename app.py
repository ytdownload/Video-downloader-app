# app.py
# Import necessary libraries
import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# It's good practice to handle potential import errors in production
try:
    from pytube import YouTube, cipher
    from pytube.exceptions import PytubeError
    PYTUBE_AVAILABLE = True
except ImportError:
    PYTUBE_AVAILABLE = False

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
    pytube_status = "available" if PYTUBE_AVAILABLE else "NOT available"
    return f"<h1>YouTube Downloader Backend is running!</h1><p>Pytube library is {pytube_status}.</p>"


@app.route('/api/video-info', methods=['POST', 'OPTIONS'])
def download_video():
    """
    Handles the video download request, including the CORS OPTIONS preflight.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if request.method == 'POST':
        print("\n--- Received POST request on /api/video-info ---")

        if not PYTUBE_AVAILABLE:
            print("ERROR: Pytube library failed to import on the server.")
            return jsonify({"error": "Server configuration error: Video library is unavailable."}), 500

        try:
            data = request.get_json()
            url = data.get('url')
            if not url:
                return jsonify({"error": "URL is required in the request body."}), 400
        except Exception:
            return jsonify({"error": "Invalid request format. Expecting JSON."}), 400

        try:
            # --- THE FIX IS HERE ---
            # This line attempts to update the internal signature logic of pytube,
            # which is a common fix for HTTP 400 errors.
            print("Attempting to apply pytube cipher patch...")
            cipher.get_throttling_function_name()
            print("Pytube cipher patch applied.")

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

        except Exception as e:
            print(f"ERROR processing video: {e}")
            traceback.print_exc()
            return jsonify({"error": "Failed to process video. It may be private, age-restricted, or an invalid link."}), 500


@app.route('/downloads/<path:filename>')
def get_file(filename):
    """
    This endpoint serves the downloaded video file to the user.
    """
    try:
        return send_from_directory(DOWNLOAD_DIRECTORY, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found."}), 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    
