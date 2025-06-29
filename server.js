const express = require('express');
const cors = require('cors');
const ytdl = require('ytdl-core');

const app = express();
const PORT = process.env.PORT || 4000;

app.use(cors());
app.use(express.json());

// POST: /api/video-info
app.post('/api/video-info', async (req, res) => {
  const { videoUrl } = req.body;

  if (!videoUrl || !ytdl.validateURL(videoUrl)) {
    return res.json({ success: false, error: 'Invalid YouTube URL' });
  }

  try {
    const info = await ytdl.getInfo(videoUrl);

    const videoFormats = info.formats
      .filter(f => f.hasVideo && f.hasAudio && f.container === 'mp4' && f.qualityLabel)
      .map(f => ({
        itag: f.itag,
        quality: f.qualityLabel
      }));

    const bestAudio = info.formats
      .filter(f => f.mimeType.includes('audio/mp4'))
      .map(f => ({
        itag: f.itag,
        quality: f.audioQuality || 'medium'
      }))[0] || null;

    res.json({
      success: true,
      title: info.videoDetails.title,
      videoFormats,
      bestAudio
    });
  } catch (error) {
    res.json({ success: false, error: 'Failed to retrieve video info' });
  }
});

// GET: /api/download?videoUrl=...&itag=...&title=...
app.get('/api/download', async (req, res) => {
  const { videoUrl, itag, title } = req.query;

  if (!videoUrl || !itag || !ytdl.validateURL(videoUrl)) {
    return res.status(400).send('Invalid download request');
  }

  try {
    res.header(
      'Content-Disposition',
      `attachment; filename="${title || 'video'}.mp4"`
    );
    ytdl(videoUrl, { filter: (format) => format.itag == itag }).pipe(res);
  } catch (error) {
    res.status(500).send('Error during download');
  }
});

// Root health check
app.get('/', (req, res) => {
  res.send('✅ YouTube Downloader API is running.');
});

app.listen(PORT, () => {
  console.log(`🚀 Server is live at http://localhost:${PORT}`);
});
