// server.js

// --- 1. Import Dependencies ---
const express = require('express');
const cors = require('cors');
const ytdl = require('@distube/ytdl-core');

// --- 2. Setup Express App ---
const app = express();
const PORT = process.env.PORT || 4000;

// --- 3. Middleware ---
app.use(cors());
app.use(express.json());

// --- 4. NEW: Root Endpoint for Status Check ---
// You can visit your Render URL (e.g., https://your-app.onrender.com/)
// to see if the server is online.
app.get('/', (req, res) => {
    res.json({
        status: 'ok',
        message: 'RapidGrab backend is running successfully.'
    });
});

// --- 5. API Endpoint to Get Video Info ---
app.post('/api/video-info', async (req, res) => {
    const { videoUrl } = req.body;

    if (!videoUrl) {
        return res.status(400).json({ success: false, error: 'Please enter a video URL.' });
    }

    // --- CRITICAL: Add Request Options to Mimic a Browser ---
    // This can help bypass YouTube's server-side blocking.
    const requestOptions = {
        headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Safari/537.36',
        },
    };

    try {
        console.log(`Fetching info for: ${videoUrl}`);
        // Pass the requestOptions to ytdl.getInfo
        const info = await ytdl.getInfo(videoUrl, { requestOptions });
        console.log('Successfully fetched video info.');

        const title = info.videoDetails.title;

        const videoFormats = ytdl.filterFormats(info.formats, 'videoandaudio')
            .filter(f => f.container === 'mp4')
            .map(format => ({
                itag: format.itag,
                quality: format.qualityLabel,
                container: format.container,
            }));

        const audioFormats = ytdl.filterFormats(info.formats, 'audioonly')
             .sort((a, b) => b.audioBitrate - a.audioBitrate);

        const bestAudio = audioFormats.length > 0 ? {
            itag: audioFormats[0].itag,
            container: audioFormats[0].container,
            quality: 'Best Audio',
        } : null;

        res.json({
            success: true,
            title: title,
            videoFormats: videoFormats,
            bestAudio: bestAudio,
        });

    } catch (error) {
        console.error('--- YTDL ERROR ---');
        console.error('Status Code:', error.statusCode);
        console.error('Message:', error.message);
        console.error('------------------');

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

// --- 6. API Endpoint to Handle the Download Stream ---
app.get('/api/download', (req, res) => {
    const { videoUrl, itag, title, container } = req.query;

    if (!videoUrl || !itag || !title) {
        return res.status(400).send('Missing required parameters for download.');
    }

    try {
        const sanitizedTitle = title.replace(/[^a-zA-Z0-9\s\-_]/g, '');
        const fileExtension = container === 'mp4' ? 'mp4' : 'mp3';
        
        res.header('Content-Disposition', `attachment; filename="${sanitizedTitle}.${fileExtension}"`);
        
        console.log(`Starting download for: ${title} (itag: ${itag})`);

        ytdl(videoUrl, {
            filter: format => format.itag == itag,
        }).pipe(res);

    } catch (error) {
        console.error('Error during download stream:', error.message);
        res.status(500).send('An error occurred during the download process.');
    }
});


// --- 7. Start the Server ---
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
