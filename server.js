// server.js

// --- 1. Import Dependencies ---
const express = require('express');
const cors = require('cors');
// Use a more robust ytdl-core fork designed for stability on servers
const ytdl = require('@distube/ytdl-core');

// --- 2. Setup Express App ---
const app = express();
// Render provides a PORT environment variable. Use it or default to 4000 for local dev.
const PORT = process.env.PORT || 4000;

// --- 3. Middleware ---
// Enable CORS for all routes, allowing your frontend to connect.
app.use(cors());
// Enable Express to parse JSON in the body of POST requests.
app.use(express.json());

// --- 4. API Endpoint to Get Video Info ---
app.post('/api/video-info', async (req, res) => {
    const { videoUrl } = req.body;

    // --- Input Validation ---
    if (!videoUrl) {
        return res.status(400).json({ success: false, error: 'Please enter a video URL.' });
    }

    try {
        // --- Fetching Video Data ---
        console.log(`Fetching info for: ${videoUrl}`);
        const info = await ytdl.getInfo(videoUrl);
        console.log('Successfully fetched video info.');

        const title = info.videoDetails.title;

        // --- Filtering for Useful Formats ---
        // Get formats with both video and audio (usually up to 720p)
        const videoFormats = ytdl.filterFormats(info.formats, 'videoandaudio')
            .filter(f => f.container === 'mp4') // Ensure it's an MP4 file
            .map(format => ({
                itag: format.itag,
                quality: format.qualityLabel,
                container: format.container,
            }));

        // Get the best available audio-only format
        const audioFormats = ytdl.filterFormats(info.formats, 'audioonly')
             .sort((a, b) => b.audioBitrate - a.audioBitrate); // Sort by bitrate to find the best

        const bestAudio = audioFormats.length > 0 ? {
            itag: audioFormats[0].itag,
            container: audioFormats[0].container,
            quality: 'Best Audio',
        } : null;

        // --- Sending Successful Response ---
        res.json({
            success: true,
            title: title,
            videoFormats: videoFormats,
            bestAudio: bestAudio,
        });

    } catch (error) {
        // --- ADVANCED ERROR HANDLING ---
        // Log the actual error on the server for debugging
        console.error('Error fetching video info:', error.message);

        // Send a specific, user-friendly error message to the frontend
        let userError = 'Failed to fetch video info. The server might be blocked or the URL is incorrect.';
        if (error.statusCode === 410) {
            userError = 'The requested video is unavailable (it may be private or deleted).';
        } else if (error.statusCode === 429) {
            userError = 'Our server is being rate-limited by YouTube. Please try again in a few minutes.';
        } else if (error.message.includes('No such video')) {
            userError = 'Invalid YouTube URL. Please check the link and try again.';
        }
        
        res.status(500).json({ success: false, error: userError });
    }
});

// --- 5. API Endpoint to Handle the Download Stream ---
app.get('/api/download', (req, res) => {
    const { videoUrl, itag, title, container } = req.query;

    // --- Query Validation ---
    if (!videoUrl || !itag || !title) {
        return res.status(400).send('Missing required parameters for download.');
    }

    try {
        // Sanitize the filename to prevent errors
        const sanitizedTitle = title.replace(/[^a-zA-Z0-9\s\-_]/g, '');
        const fileExtension = container === 'mp4' ? 'mp4' : 'mp3';
        
        // Set headers to trigger a download in the browser
        res.header('Content-Disposition', `attachment; filename="${sanitizedTitle}.${fileExtension}"`);
        
        console.log(`Starting download for: ${title} (itag: ${itag})`);

        // Create the download stream and pipe it directly to the user's browser
        // This is memory-efficient as the file is never stored on the server
        ytdl(videoUrl, {
            filter: format => format.itag == itag,
        }).pipe(res);

    } catch (error) {
        console.error('Error during download stream:', error.message);
        res.status(500).send('An error occurred during the download process.');
    }
});


// --- 6. Start the Server ---
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
    console.log('Open index.html to use the application.');
});

