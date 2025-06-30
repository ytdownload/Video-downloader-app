// server.js

const express = require('express');
const cors = require('cors');
const YTDlpWrap = require('yt-dlp-wrap').default;
const path = require('path');
const fs = require('fs');

// --- Initialize App and yt-dlp ---
const app = express();
const PORT = process.env.PORT || 4000;
const ytDlpWrap = new YTDlpWrap();

// --- CRITICAL: Download yt-dlp on Server Start ---
// This is a more robust way to ensure yt-dlp is available.
(async () => {
    try {
        // Get the path where yt-dlp should be.
        const ytDlpPath = YTDlpWrap.getBinaryPath();
        
        // Check if the file already exists.
        if (fs.existsSync(ytDlpPath)) {
            console.log('yt-dlp binary already exists.');
        } else {
            console.log('yt-dlp binary not found, starting download...');
            // If it doesn't exist, download it.
            await YTDlpWrap.downloadFromGithub();
            console.log('yt-dlp binary downloaded successfully.');
        }
    } catch (error) {
        console.error('Failed to download yt-dlp binary:', error);
        // If download fails, the app can't work, so we exit.
        process.exit(1);
    }
})();


// --- Middleware ---
app.use(cors());
app.use(express.json());

// --- A simple status check endpoint ---
app.get('/', (req, res) => {
    res.json({ status: 'ok', message: 'yt-dlp backend is running.' });
});

// --- API Endpoint to Get Video Info ---
app.post('/api/video-info', async (req, res) => {
    const { videoUrl } = req.body;

    if (!videoUrl) {
        return res.status(400).json({ success: false, error: 'Video URL is required.' });
    }

    try {
        console.log(`Fetching metadata for: ${videoUrl}`);
        const metadata = await ytDlpWrap.getVideoInfo(videoUrl);
        res.json({ success: true, data: metadata });

    } catch (error) {
        console.error('Error fetching video info with yt-dlp:', error.message);
        res.status(500).json({ success: false, error: 'Failed to fetch video information. The URL may be invalid or the video is private.' });
    }
});

// --- API Endpoint to Trigger a Download ---
app.get('/api/download', async (req, res) => {
    const { videoUrl, formatId } = req.query;

    if (!videoUrl || !formatId) {
        return res.status(400).send('Missing required query parameters: videoUrl and formatId.');
    }

    try {
        console.log(`Getting download link for format: ${formatId}`);
        const downloadUrl = await ytDlpWrap.getUrl(videoUrl, ['-f', formatId]);
        res.redirect(downloadUrl);

    } catch (error) {
        console.error('Error getting download URL:', error.message);
        res.status(500).send('An error occurred while preparing the download link.');
    }
});


// --- Start the Server ---
app.listen(PORT, () => {
    console.log(`yt-dlp API server is running on port ${PORT}`);
});
