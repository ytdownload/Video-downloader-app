# app.py
# Import necessary libraries
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pytube import YouTube
from pytube.exceptions import PytubeError

# --- Configuration for Production (Render) ---
DOWNLOAD_DIRECTORY = os.environ.get('DOWNLOAD_DIR', 'downloads')

# --- Flask App Initialization ---
app = Flask(__name__)

# --- CORS Configuration (Final and Secure) ---
# Based on your frontend URL, we are now explicitly allowing ONLY
# your GitHub Pages site to make requests. This is the correct and
# secure way to configure CORS for a production application.
origins = [
    "https://ytdownload.github.io"
]
CORS(app, origins=origins, supports_credentials=True)


# --- Server Setup ---
def setup_server():
    """Creates the download directory if it doesn't exist."""
    if not os.path.exists(DOWNLOAD_DIRECTORY):
        try:
            os.makedirs(DOWNLOAD_DIRECTORY)
            print(f"Successfully created download directory at: {DOWNLOAD_DIRECTORY}")
        except OSError as e:
            print(f"Error creating directory {DOWNLOAD_DIRECTORY}: {e}")
            raise

setup_server()

# --- API Endpoints ---

@app.route('/')
def index():
    """A simple root endpoint to confirm the backend is running."""
    return "<h1>YouTube Downloader Backend is running!</h1><p>CORS is correctly configured for ytdownload.github.io.</p>"

@app.route('/api/download', methods=['POST'])
def download_video():
    """
    This is the main endpoint for handling video downloads.
    """
    print("Received a download request.")

    try:
        data = request.get_json()
        if not data or 'url' not in data:
            print("Error: Invalid or missing JSON payload with 'url' key.")
            return jsonify({"error": "URL is required in JSON payload"}), 400
        url = data['url']
    except Exception as e:
        print(f"Error parsing request JSON: {e}")
        return jsonify({"error": "Invalid request format. Expecting JSON with a 'url' key."}), 400

    print(f"Attempting to download video from: {url}")

    try:
        yt = YouTube(url)
        stream = yt.streams.get_highest_resolution()

        if not stream:
            print(f"Error: No downloadable stream found for URL: {url}")
            return jsonify({"error": "No downloadable stream found for this video."}), 404

        print(f"Downloading '{yt.title}'...")
        stream.download(output_path=DOWNLOAD_DIRECTORY)
        filename = stream.default_filename
        print(f"Successfully downloaded '{filename}' to '{DOWNLOAD_DIRECTORY}'")

        return jsonify({
            "message": "Download successful!",
            "filename": filename,
            "video_title": yt.title,
            "thumbnail_url": yt.thumbnail_url
        }), 200

    except PytubeError as e:
        error_message = f"An error occurred with the video service: {str(e)}"
        print(f"Error for URL '{url}': {error_message}")
        return jsonify({"error": error_message}), 500

    except Exception as e:
        error_message = f"An unexpected server error occurred: {str(e)}"
        print(f"Error for URL '{url}': {error_message}")
        return jsonify({"error": "An unexpected server error occurred. Please try again later."}), 500


@app.route('/downloads/<path:filename>')
def get_file(filename):
    """
    This endpoint serves the downloaded video file to the user.
    """
    print(f"Serving file: {filename} from {DOWNLOAD_DIRECTORY}")
    try:
        return send_from_directory(DOWNLOAD_DIRECTORY, filename, as_attachment=True)
    except FileNotFoundError:
        print(f"Error: Requested file not found: {filename}")
        return jsonify({"error": "File not found. It may have been moved or deleted."}), 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask server for local development at http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
    
