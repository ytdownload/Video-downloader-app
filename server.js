// server.js

const express = require('express');
const cors = require('cors');
const fetch = require('node-fetch');

const app = express();
const PORT = process.env.PORT || 4000;

app.use(cors());
app.use(express.json());

// --- A list of reliable public APIs to try in order ---
const API_ENDPOINTS = [
    'https://invidious.io.lol/api/v1/videos/',
    'https://vid.puffyan.us/api/v1/videos/',
    'https://inv.hnh.is/api/v1/videos/',
    'https://invidious.projectsegfau.lt/api/v1/videos/'
];

// A simple status check endpoint
app.get('/', (req, res) => {
    res.json({ status: 'ok', message: 'Proxy backend with fallbacks is running.' });
});

app.post('/api/video-info', async (req, res) => {
    const { videoId } = req.body;

    if (!videoId) {
        return res.status(400).json({ success: false, error: 'Video ID is required.' });
    }

    // --- NEW: Loop through the API list ---
    for (const endpoint of API_ENDPOINTS) {
        try {
            const fullApiUrl = `${endpoint}${videoId}`;
            console.log(`Proxying request to: ${fullApiUrl}`);

            const apiResponse = await fetch(fullApiUrl, { timeout: 7000 }); // 7-second timeout

            if (!apiResponse.ok) {
                // If this server gives an error, log it and the loop will try the next one.
                throw new Error(`API responded with status: ${apiResponse.status}`);
            }

            const data = await apiResponse.json();
            
            // If we get here, the request was successful.
            // Send the successful response back to our frontend and exit the loop.
            console.log(`Success with ${endpoint}`);
            return res.json({ success: true, data: data });

        } catch (error) {
            console.error(`Failed to fetch from ${endpoint}:`, error.message);
            // This error is expected if a server is down. The loop will continue.
        }
    }

    // If the loop finishes and we never had a success, it means all servers failed.
    console.error('All public APIs failed.');
    res.status(502).json({ success: false, error: 'All download servers are currently busy or unavailable. Please try again later.' });
});

app.listen(PORT, () => {
    console.log(`Proxy server is running on port ${PORT}`);
});
