# app.py

import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pytube import YouTube, cipher
from pytube.exceptions import PytubeError
import io
import re # Import the regular expressions module

# --- App Factory Pattern for Production Stability ---
def create_app():
    """Creates and configures the Flask app."""
    app = Flask(__name__)
    CORS(app)

    # --- CRITICAL FIX for 'HTTP Error 400: Bad Request' ---
    # Pytube can fail on certain videos because of YouTube's cipher protection.
    # This patch manually updates the cipher regex to the latest known working version.
    try:
        print("Applying Pytube cipher patch...")
        var_regex = re.compile(r"^\$*\w+\W")
        cipher.get_transform_function_name = lambda js: (
            var_regex.search(js).group(0)[:-1]
        )
        print("Pytube cipher patch applied successfully.")
    except Exception as e:
        print(f"Could not apply Pytube cipher patch: {e}")


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
        if not data:
            return jsonify({"success": False, "error": "Invalid request format."}), 400
        
        video_url = data.get('videoUrl')
        if not video_url:
            return jsonify({"success": False, "error": "Video URL is required."}), 400

        try:
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
            print(f"Pytube Error: {str(e)}")
            return jsonify({"success": False, "error": "Pytube Error: The URL might be invalid, private, or age-restricted. YouTube may also be temporarily blocking our server."}), 500
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            # Check if the error is the one we are trying to fix
            if "HTTP Error 400" in str(e):
                 return jsonify({"success": False, "error": "Failed to process video due to YouTube API changes. The patch may need updating."}), 500
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

            sanitized_title = "".join([c for c in title if c.isalnum() or c.isspace()]).rstrip()
            
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
app = create_app()

# This block is only for running the app on your local computer.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
