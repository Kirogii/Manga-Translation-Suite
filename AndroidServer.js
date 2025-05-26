const express = require('express');
const localtunnel = require('localtunnel');

const app = express();
const PORT = 8000;

// Set to a subdomain name or '' for random
const CUSTOM_SUBDOMAIN = ''; // ← Change this or leave blank for random (some lengths dont work sometimes)

app.get('/', (req, res) => res.send('Hello from LocalTunnel!'));

app.listen(PORT, async () => {
  console.log(`Local server running at http://localhost:${PORT}`);

  const subdomain = CUSTOM_SUBDOMAIN.trim();
  const options = {
    port: PORT,
    ...(subdomain && { subdomain }), // Only include if non-empty
  };

  console.log(`\n🌀 Attempting to create tunnel...`);
  if (subdomain) console.log(`🔗 Requested subdomain: "${subdomain}"`);
  else console.log(`🎲 Using random subdomain`);

  try {
    const timeout = setTimeout(() => {
      console.error('⏳ Tunnel creation taking too long. Check your internet or subdomain.');
    }, 8000);

    const tunnel = await localtunnel(options);
    clearTimeout(timeout);

    console.log('\n🛡️ LocalTunnel Active');
    console.log(`🌐 Public URL: ${tunnel.url}\n`);

    tunnel.on('close', () => {
      console.log('LocalTunnel connection closed.');
    });
  } catch (err) {
    console.error('❌ Failed to start LocalTunnel:', err);
  }
});
