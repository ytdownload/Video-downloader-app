# app.py

import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pytube import YouTube
from pytube.exceptions import PytubeError
import io

# 1. Initialize Flask App
app = Flask(__name__)
# Enable CORS to allow your frontend to make requests to this backend
CORS(app)

# 2. Root Endpoint for Status Check
# Visit your Render URL to see this message, confirming the server is online.
@app.route('/')
def index():
    return jsonify({
        "status": "ok",
        "message": "Python Flask backend for RapidGrab is running."
    })

# 3. API Endpoint to Get Video Info
@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    data = request.get_json()
    video_url = data.get('videoUrl')

    if not video_url:
        return jsonify({"success": False, "error": "Video URL is required."}), 400

    try:
        # Create a YouTube object
        yt = YouTube(video_url)
        
        # --- Filter for useful formats ---
        # Get video streams with both audio and video, in MP4 format
        video_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
        
        # Get the best audio-only stream
        audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

        # --- Format the data for the frontend ---
        video_formats = [
            {
                "itag": stream.itag,
                "quality": stream.resolution,
                "container": "mp4"
            } for stream in video_streams
        ]

        best_audio = {
            "itag": audio_stream.itag,
            "quality": "Best Audio",
            "container": "mp4" # Pytube often downloads audio in mp4 container
        } if audio_stream else None

        return jsonify({
            "success": True,
            "title": yt.title,
            "videoFormats": video_formats,
            "bestAudio": best_audio
        })

    except PytubeError as e:
        # Handle specific Pytube errors
        print(f"Pytube Error: {e}")
        error_message = "Failed to fetch video info. The URL might be invalid, private, or age-restricted."
        return jsonify({"success": False, "error": error_message}), 500
    except Exception as e:
        # Handle other potential errors (e.g., network issues)
        print(f"An unexpected error occurred: {e}")
        return jsonify({"success": False, "error": "An unexpected server error occurred."}), 500

# 4. API Endpoint to Handle the Download
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

        # Create a buffer in memory to hold the video data
        buffer = io.BytesIO()
        stream.stream_to_buffer(buffer)
        buffer.seek(0) # Rewind the buffer to the beginning

        # Sanitize filename
        sanitized_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c.isspace()]).rstrip()
        
        # Send the buffer as a file attachment
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{sanitized_title}.mp4",
            mimetype=stream.mime_type
        )

    except Exception as e:
        print(f"Error during download: {e}")
        return "An error occurred during the download.", 500

# 5. Run the App
# This part is for local development. Render will use a Gunicorn server instead.
if __name__ == '__main__':
    # Use the PORT environment variable if available, otherwise default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
