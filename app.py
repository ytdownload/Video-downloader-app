# app.py

import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pytube import YouTube
from pytube.exceptions import PytubeError
import io

# --- Best Practice: App Factory Pattern ---
defdef create_app():
    """Creates and configures the Flask app."""
    print("Initializing Flask app...")
    app = Flask(__name__)
    
    # Enable CORS to allow your frontend to make requests to this backend
    CORS(app)
    print("CORS has been configured.")

    # --- Root Endpoint for Status Check ---
    @app.route('/')
    def index():
        return jsonify({
            "status": "ok",
            "message": "Python Flask backend for RapidGrab is running."
        })

    # --- API Endpoint to Get Video Info ---
    @app.route('/api/video-info', methods=['POST'])
    def get_video_info():
        data = request.get_json()
        video_url = data.get('videoUrl')

        if not video_url:
            return jsonify({"success": False, "error": "Video URL is required."}), 400

        try:
            print(f"Received request for URL: {video_url}")
            yt = YouTube(video_url)
            
            video_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

            video_formats = [{"itag": s.itag, "quality": s.resolution, "container": "mp4"} for s in video_streams]
            best_audio = {"itag": audio_stream.itag, "quality": "Best Audio", "container": "mp4"} if audio_stream else None

            print(f"Successfully fetched info for title: {yt.title}")
            return jsonify({
                "success": True,
                "title": yt.title,
                "videoFormats": video_formats,
                "bestAudio": best_audio
            })

        except PytubeError as e:
            print(f"Pytube Error: {str(e)}")
            return jsonify({"success": False, "error": "Pytube Error: The URL might be invalid, private, or age-restricted."}), 500
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return jsonify({"success": False, "error": "An unexpected server error occurred."}), 500

    # --- API Endpoint to Handle the Download ---
    @app.route('/api/download')
    def download_video():
        video_url = request.args.get('videoUrl')
        itag = request.args.get('itag')
        title = request.args.get('title')

        if not video_url or not itag:
            return "Missing URL or itag parameter", 400

        try:
            yt = YouTube(video_url)
            stream = yt.streams.get_by_itag(int(itag))

            buffer = io.BytesIO()
            stream.stream_to_buffer(buffer)
            buffer.seek(0)

            sanitized_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c.isspace()]).rstrip()
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"{sanitized_title}.mp4",
                mimetype=stream.mime_type
            )
        except Exception as e:
            print(f"Error during download: {str(e)}")
            return "An error occurred during the download.", 500
            
    print("Flask app setup complete.")
    return app

# --- Create the app instance ---
# Gunicorn will look for this 'app' variable by default.
app = create_app()

# The following block is for local development only.
# Render and Gunicorn will NOT run this.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Note: host='0.0.0.0' is important for Docker/cloud environments.
    app.run(host='0.0.0.0', port=port)

