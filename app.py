# app.py
# Import necessary libraries
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pytube import YouTube
from pytube.exceptions import PytubeError

# --- Configuration for Production (Render) ---
# On platforms like Render, the filesystem is ephemeral. We need to use a
# persistent disk for storing downloaded videos. Render allows you to mount
# a disk at a specific path. We'll read this path from an environment
# variable, defaulting to a local 'downloads' folder for development.
DOWNLOAD_DIRECTORY = os.environ.get('DOWNLOAD_DIR', 'downloads')

# --- Flask App Initialization ---
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing (CORS) to allow your frontend
# to communicate with this backend.
CORS(app)

# --- Server Setup ---
# This function ensures the download directory exists when the app starts.
# It's crucial for both local development and the Render environment.
def setup_server():
    """Creates the download directory if it doesn't exist."""
    if not os.path.exists(DOWNLOAD_DIRECTORY):
        try:
            os.makedirs(DOWNLOAD_DIRECTORY)
            print(f"Successfully created download directory at: {DOWNLOAD_DIRECTORY}")
        except OSError as e:
            print(f"Error creating directory {DOWNLOAD_DIRECTORY}: {e}")
            # If the directory can't be created, the app can't function.
            # It's better to raise the exception to stop the launch.
            raise

# Call the setup function when the app is initialized.
setup_server()

# --- API Endpoints ---

@app.route('/')
def index():
    """
    A simple root endpoint to confirm the backend is running.
    Helpful for checking if the deployment was successful.
    """
    return "<h1>YouTube Downloader Backend is running!</h1><p>Use the /api/download endpoint to download videos.</p>"

@app.route('/api/download', methods=['POST'])
def download_video():
    """
    This is the main endpoint for handling video downloads.
    It receives a YouTube URL, downloads the video to the persistent disk,
    and returns information about the downloaded file to the frontend.
    """
    print("Received a download request.")

    # 1. Get the URL from the incoming JSON request
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

    # 2. Use pytube to download the video
    try:
        yt = YouTube(url)

        # Get the highest resolution progressive stream (video + audio)
        stream = yt.streams.get_highest_resolution()

        if not stream:
            print(f"Error: No downloadable stream found for URL: {url}")
            return jsonify({"error": "No downloadable stream found for this video."}), 404

        print(f"Found stream: {stream.resolution}, {stream.mime_type}")
        print(f"Downloading '{yt.title}'...")

        # Download the stream to our specified directory (the persistent disk on Render)
        stream.download(output_path=DOWNLOAD_DIRECTORY)
        filename = stream.default_filename
        print(f"Successfully downloaded '{filename}' to '{DOWNLOAD_DIRECTORY}'")

        # 3. Return a success response to the frontend
        return jsonify({
            "message": "Download successful!",
            "filename": filename,
            "video_title": yt.title,
            "thumbnail_url": yt.thumbnail_url
        }), 200

    except PytubeError as e:
        # Handle specific errors from the pytube library (e.g., video unavailable, age restricted)
        error_message = f"An error occurred with the video service: {str(e)}"
        print(f"Error for URL '{url}': {error_message}")
        return jsonify({"error": error_message}), 500

    except Exception as e:
        # Handle any other unexpected errors during the process
        error_message = f"An unexpected server error occurred: {str(e)}"
        print(f"Error for URL '{url}': {error_message}")
        return jsonify({"error": "An unexpected server error occurred. Please try again later."}), 500


@app.route('/downloads/<path:filename>')
def get_file(filename):
    """
    This endpoint serves the downloaded video file to the user from the persistent disk.
    """
    print(f"Serving file: {filename} from {DOWNLOAD_DIRECTORY}")
    try:
        # send_from_directory is a secure way to send files from a known directory.
        # as_attachment=True prompts the user's browser to download the file.
        return send_from_directory(DOWNLOAD_DIRECTORY, filename, as_attachment=True)
    except FileNotFoundError:
        print(f"Error: Requested file not found: {filename}")
        return jsonify({"error": "File not found. It may have been moved or deleted."}), 404


# This block is for local development only.
# When deploying on Render, Gunicorn will be used to run the app.
if __name__ == '__main__':
    # The port is read from an environment variable, which Render sets automatically.
    # It defaults to 5000 for local development.
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask server for local development at http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
