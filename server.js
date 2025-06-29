// server.js

// --- 1. Import Dependencies ---
const express = require('express');
const cors = require('cors');
const play = require('play-dl');

// --- 2. Setup Express App ---
const app = express();
const PORT = process.env.PORT || 4000;

// --- 3. Middleware ---
app.use(cors());
app.use(express.json());

// --- 4. CRITICAL FIX: Refresh play-dl Authorization on Start ---
// This attempts to get fresh, unblocked cookies from YouTube when the server starts.
(async () => {
    try {
        console.log("Refreshing play-dl authorization...");
        await play.authorization();
        console.log("play-dl authorization refreshed successfully.");
    } catch (e) {
        console.error("Failed to refresh play-dl authorization:", e);
    }
})();


// --- 5. Root Endpoint for Status Check ---
app.get('/', (req, res) => {
    res.json({
        status: 'ok',
        message: 'Node.js backend with play-dl is running.'
    });
});

// --- 6. API Endpoint to Get Video Info ---
app.post('/api/video-info', async (req, res) => {
    const { videoUrl } = req.body;

    if (!videoUrl) {
        return res.status(400).json({ success: false, error: 'Video URL is required.' });
    }

    try {
        console.log(`Fetching info for: ${videoUrl}`);
        if (play.yt_validate(videoUrl) !== 'video') {
             return res.status(400).json({ success: false, error: 'Invalid or unsupported YouTube URL.' });
        }

        const videoInfo = await play.video_info(videoUrl);
        const title = videoInfo.video_details.title;
        console.log(`Successfully fetched info for: ${title}`);

        const videoFormats = videoInfo.format
            .filter(f => f.mime_type.includes('mp4') && f.audio_channels > 0)
            .map(format => ({
                itag: format.itag,
                quality: format.quality_label,
                container: 'mp4',
            }));
        
        const audioFormats = videoInfo.format
            .filter(f => f.mime_type.includes('audio/mp4'))
            .sort((a, b) => b.bitrate - a.bitrate);

        res.json({
            success: true,
            title: title,
            videoFormats: videoFormats,
            bestAudio: audioFormats.length > 0 ? {
                itag: audioFormats[0].itag,
                container: 'mp4',
                quality: 'Best Audio',
            } : null,
        });

    } catch (error) {
        console.error('--- PLAY-DL ERROR ---');
        console.error(error.message); // Log the specific error message
        res.status(500).json({ success: false, error: 'Failed to fetch video info. The server is likely being blocked by YouTube.' });
    }
});

// --- 7. API Endpoint to Handle the Download Stream ---
app.get('/api/download', async (req, res) => {
    const { videoUrl, itag, title } = req.query;

    if (!videoUrl || !itag || !title) {
        return res.status(400).send('Missing required parameters for download.');
    }
    
    try {
        console.log(`Starting download for: ${title} (itag: ${itag})`);
        const stream = await play.stream(videoUrl, {
            itag: itag
        });

        const sanitizedTitle = title.replace(/[^a-zA-Z0-9\s\-_]/g, '');
        
        res.header('Content-Disposition', `attachment; filename="${sanitizedTitle}.mp4"`);
        res.header('Content-Type', stream.type);

        stream.stream.pipe(res);

    } catch (error) {
        console.error('Error during download stream:', error);
        res.status(500).send('An error occurred during the download process.');
    }
});


// --- 8. Start the Server ---
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
