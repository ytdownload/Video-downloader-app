# app.py

import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pytube import YouTube
from pytube.exceptions import PytubeError
import io

# --- App Factory Pattern for Production Stability ---
def create_app():
    """Creates and configures the Flask app."""
    # This is the main app object
    app = Flask(__name__)
    
    # Configure CORS to allow requests from your frontend
    CORS(app)

    # --- Root Endpoint for Status Check ---
    # A simple way to see if the server is online
    @app.route('/')
    def index():
        return jsonify({
            "status": "ok",
            "message": "Python Flask backend for RapidGrab is running."
        })

    # --- API Endpoint to Get Video Info ---
    @app.route('/api/video-info', methods=['POST'])
    def get_video_info():
        # Get the JSON data sent from the frontend
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid request format."}), 400
        
        video_url = data.get('videoUrl')
        if not video_url:
            return jsonify({"success": False, "error": "Video URL is required."}), 400

        try:
            # Create a YouTube object from the URL
            yt = YouTube(video_url)
            
            # Get available video and audio streams
            video_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

            # Format the data to be sent back to the frontend
            video_formats = [{"itag": s.itag, "quality": s.resolution, "container": "mp4"} for s in video_streams]
            best_audio = {"itag": audio_stream.itag, "quality": "Best Audio", "container": "mp4"} if audio_stream else None

            return jsonify({
                "success": True,
                "title": yt.title,
                "videoFormats": video_formats,
                "bestAudio": best_audio
            })

        except PytubeError as e:
            # Handle errors from the pytube library
            print(f"Pytube Error: {str(e)}")
            return jsonify({"success": False, "error": "Pytube Error: The URL might be invalid, private, or age-restricted."}), 500
        except Exception as e:
            # Handle any other unexpected errors
            print(f"An unexpected error occurred: {str(e)}")
            return jsonify({"success": False, "error": "An unexpected server error occurred."}), 500

    # --- API Endpoint to Handle the Download ---
    @app.route('/api/download')
    def download_video():
        # Get parameters from the URL (e.g., ?videoUrl=...&itag=...)
        video_url = request.args.get('videoUrl')
        itag = request.args.get('itag')
        title = request.args.get('title')

        if not video_url or not itag:
            return "Missing URL or itag parameter", 400

        try:
            yt = YouTube(video_url)
            stream = yt.streams.get_by_itag(int(itag))

            # Download the video to a memory buffer instead of a file
            buffer = io.BytesIO()
            stream.stream_to_buffer(buffer)
            buffer.seek(0)

            # Clean the title to create a valid filename
            sanitized_title = "".join([c for c in title if c.isalnum() or c.isspace()]).rstrip()
            
            # Send the buffer as a file for the user to download
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"{sanitized_title}.mp4",
                mimetype=stream.mime_type
            )
        except Exception as e:
            print(f"Error during download: {str(e)}")
            return "An error occurred during the download.", 500
            
    return app

# --- Create the app instance for Gunicorn ---
# This is the variable Gunicorn will look for.
app = create_app()

# This block is only for running the app on your local computer.
# Render will NOT use this part.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
        
