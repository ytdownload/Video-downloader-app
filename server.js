const express = require('express');
const { exec } = require('child_process');
const cors = require('cors');

const app = express();
app.use(cors());

app.get('/video', (req, res) => {
  const videoUrl = req.query.link;
  if (!videoUrl) return res.status(400).json({ error: 'Missing video link' });

  const command = `yt-dlp -j "${videoUrl}"`;

  exec(command, (error, stdout, stderr) => {
    if (error) {
      return res.status(500).json({ error: stderr });
    }

    try {
      const json = JSON.parse(stdout);
      const formats = json.formats.map(f => ({
        quality: f.format_note,
        url: f.url,
        ext: f.ext,
        resolution: f.resolution || `${f.height}p`
      }));
      res.json({ title: json.title, thumbnail: json.thumbnail, formats });
    } catch (err) {
      res.status(500).json({ error: 'Failed to parse video info' });
    }
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
