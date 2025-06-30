// server.js

const express = require('express');
const cors = require('cors');
const YTDlpWrap = require('yt-dlp-wrap').default;

// --- Initialize App and yt-dlp ---
const app = express();
const PORT = process.env.PORT || 4000;
const ytDlpWrap = new YTDlpWrap();

// --- CRITICAL FIX: Download yt-dlp on Server Start ---
// This simpler method is more robust and avoids the previous crash.
(async () => {
    try {
        console.log('Downloading latest yt-dlp binary...');
        // This command is safe to run every time. It will only download if needed.
        await YTDlpWrap.downloadFromGithub();
        console.log('yt-dlp binary is ready.');
    } catch (error) {
        console.error('FATAL: Failed to download yt-dlp binary:', error);
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
