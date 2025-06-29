// server.js

// --- 1. Import Dependencies ---
const express = require('express');
const cors = require('cors');
// Use the most robust ytdl-core fork
const ytdl = require('@distube/ytdl-core');

// --- 2. Setup Express App ---
const app = express();
const PORT = process.env.PORT || 4000;

// --- 3. Middleware ---
app.use(cors());
app.use(express.json());

// --- 4. Root Endpoint for Status Check ---
app.get('/', (req, res) => {
    res.json({
        status: 'ok',
        message: 'Node.js backend for RapidGrab is running.'
    });
});

// --- 5. API Endpoint to Get Video Info ---
app.post('/api/video-info', async (req, res) => {
    const { videoUrl } = req.body;

    if (!videoUrl) {
        return res.status(400).json({ success: false, error: 'Video URL is required.' });
    }

    try {
        console.log(`Fetching info for: ${videoUrl}`);
        const info = await ytdl.getInfo(videoUrl);
        console.log(`Successfully fetched info for: ${info.videoDetails.title}`);

        const videoFormats = ytdl.filterFormats(info.formats, 'videoandaudio')
            .filter(f => f.container === 'mp4')
            .map(format => ({
                itag: format.itag,
                quality: format.qualityLabel,
                container: format.container,
            }));
        
        const audioFormats = ytdl.filterFormats(info.formats, 'audioonly')
             .sort((a, b) => b.audioBitrate - a.audioBitrate);

        res.json({
            success: true,
            title: info.videoDetails.title,
            videoFormats: videoFormats,
            bestAudio: audioFormats.length > 0 ? {
                itag: audioFormats[0].itag,
                container: audioFormats[0].container,
                quality: 'Best Audio',
            } : null,
        });

    } catch (error) {
        console.error('--- YTDL ERROR ---');
        console.error(error);
        res.status(500).json({ success: false, error: 'Failed to fetch video info. The video may be private, age-restricted, or YouTube is blocking our server.' });
    }
});

// --- 6. API Endpoint to Handle the Download Stream ---
app.get('/api/download', (req, res) => {
    const { videoUrl, itag, title } = req.query;

    if (!videoUrl || !itag || !title) {
        return res.status(400).send('Missing required parameters for download.');
    }
    
    try {
        const sanitizedTitle = title.replace(/[^a-zA-Z0-9\s\-_]/g, '');
        
        res.header('Content-Disposition', `attachment; filename="${sanitizedTitle}.mp4"`);
        
        console.log(`Starting download for: ${title} (itag: ${itag})`);
        ytdl(videoUrl, {
            filter: format => format.itag == itag,
        }).pipe(res);

    } catch (error) {
        console.error('Error during download stream:', error);
        res.status(500).send('An error occurred during the download process.');
    }
});


// --- 7. Start the Server ---
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
