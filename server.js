const fetch = (...args) => import('node-fetch').then(({ default: fetch }) => fetch(...args));

app.post('/api/video-info', async (req, res) => {
  const { videoUrl } = req.body;
  if (!videoUrl) return res.json({ success: false, error: 'No URL provided' });

  try {
    const apiRes = await fetch(`https://you-link-api.vercel.app/?url=${encodeURIComponent(videoUrl)}`);
    const data = await apiRes.json();

    if (!data.title || !data.download) {
      return res.json({ success: false, error: 'Invalid response from API' });
    }

    const videoFormats = data.download.filter(x => x.type === 'video').map(f => ({
      itag: f.url, // use direct link
      quality: f.quality || f.subname || f.sub
    }));

    const bestAudio = data.download.find(x => x.type === 'audio');

    res.json({
      success: true,
      title: data.title,
      videoFormats,
      bestAudio: bestAudio
        ? { itag: bestAudio.url, quality: bestAudio.quality || 'Audio' }
        : null
    });
  } catch (err) {
    res.json({ success: false, error: 'Proxy API failed' });
  }
});
