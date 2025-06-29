// Updated YouTube Downloader Backend to match frontend expectations

const express = require('express'); const cors = require('cors'); const ytdl = require('ytdl-core'); const app = express();

const PORT = process.env.PORT || 4000;

app.use(cors()); app.use(express.json());

// POST endpoint for fetching video info app.post('/api/video-info', async (req, res) => { const { videoUrl } = req.body;

if (!videoUrl || !ytdl.validateURL(videoUrl)) { return res.json({ success: false, error: 'Invalid YouTube URL' }); }

try { const info = await ytdl.getInfo(videoUrl); const videoFormats = info.formats .filter(f => f.hasAudio && f.hasVideo && f.container === 'mp4' && f.qualityLabel) .map(f => ({ itag: f.itag, quality: f.qualityLabel }));

const audioFormats = info.formats.filter(f => f.mimeType.includes('audio/mp4'));
const bestAudio = audioFormats.length > 0 ? {
  itag: audioFormats[0].itag,
  quality: audioFormats[0].audioQuality || 'medium'
} : null;

res.json({
  success: true,
  title: info.videoDetails.title,
  videoFormats,
  bestAudio
});

} catch (error) { res.json({ success: false, error: 'Failed to retrieve video info' }); } });

// GET endpoint to stream/download video or audio by itag app.get('/api/download', async (req, res) => { const { videoUrl, itag, title } = req.query;

if (!videoUrl || !itag || !ytdl.validateURL(videoUrl)) { return res.status(400).send('Invalid request'); }

try { res.header('Content-Disposition', attachment; filename="${title || 'video'}.mp4"); ytdl(videoUrl, { filter: format => format.itag == itag }).pipe(res); } catch (error) { res.status(500).send('Error downloading file'); } });

// Default route app.get('/', (req, res) => { res.send('YouTube Downloader API is running.'); });

app.listen(PORT, () => { console.log(Server running at http://localhost:${PORT}); });

