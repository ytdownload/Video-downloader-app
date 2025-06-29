// server.js

const express = require('express');
const cors = require('cors');
// Use require() which is more standard for this type of project
const fetch = require('node-fetch');

const app = express();
const PORT = process.env.PORT || 4000;

app.use(cors());
app.use(express.json());

// The public API we will call from our server
const API_ENDPOINT = 'https://invidious.io.lol/api/v1/videos/';

// A simple status check endpoint
app.get('/', (req, res) => {
    res.json({ status: 'ok', message: 'Proxy backend is running.' });
});

app.post('/api/video-info', async (req, res) => {
    const { videoId } = req.body;

    if (!videoId) {
        return res.status(400).json({ success: false, error: 'Video ID is required.' });
    }

    try {
        const fullApiUrl = `${API_ENDPOINT}${videoId}`;
        console.log(`Proxying request to: ${fullApiUrl}`);

        // Our server calls the public API
        const apiResponse = await fetch(fullApiUrl);

        if (!apiResponse.ok) {
            throw new Error(`Public API responded with status: ${apiResponse.status}`);
        }

        const data = await apiResponse.json();
        
        // Send the successful response back to our frontend
        res.json({ success: true, data: data });

    } catch (error) {
        console.error('Proxy Error:', error.message);
        res.status(500).json({ success: false, error: 'Failed to fetch video info from the public API.' });
    }
});

app.listen(PORT, () => {
    console.log(`Proxy server is running on port ${PORT}`);
});
