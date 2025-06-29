// server.js
// This is the backend for the video downloader application.

// Import required modules
const express = require('express');
const ytdl = require('ytdl-core');
const path = require('path');
const cors = require('cors'); // <-- 1. IMPORT THE CORS PACKAGE

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3000;

// --- Middleware ---

// <-- 2. USE THE CORS MIDDLEWARE -->
// This must be placed before your API routes. It allows all origins.
app.use(cors()); 

// Serve static files from the 'public' directory (for our HTML, CSS, JS)
app.use(express.static(path.join(__dirname, 'public')));
// Enable Express to parse JSON in request bodies
app.use(express.json());

// --- API Endpoints ---

/**
 * @route   GET /video-info
 * @desc    Fetches video information (title, formats, etc.) from a YouTube URL.
 * @access  Public
 */
app.get('/video-info', async (req, res) => {
    // Get the video URL from the query parameters
    const { videoURL } = req.query;

    // Validate the URL
    if (!videoURL || !ytdl.validateURL(videoURL)) {
        return res.status(400).json({ success: false, error: 'Please provide a valid YouTube URL.' });
    }

    try {
        // Fetch video information using ytdl-core
        const info = await ytdl.getInfo(videoURL);
        
        // Extract relevant information
        const title = info.videoDetails.title;
        const thumbnail = info.videoDetails.thumbnails[info.videoDetails.thumbnails.length - 1].url; // Get highest quality thumbnail

        // Filter for formats with both video and audio, and audio-only formats
        const formats = info.formats.map(format => ({
            itag: format.itag,
            quality: format.qualityLabel || format.audioBitrate + 'kbps',
            container: format.container,
            hasVideo: format.hasVideo,
            hasAudio: format.hasAudio,
            url: format.url, // The direct download URL
        }));

        // Send the extracted information back to the client
        res.json({
            success: true,
            title,
            thumbnail,
            formats,
        });

    } catch (error) {
        console.error('Error fetching video info:', error.message);
        res.status(500).json({ success: false, error: 'Failed to fetch video information. The video might be private, age-restricted, or unavailable.' });
    }
});

// --- Server Activation ---

// Start the server and listen on the specified port
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
