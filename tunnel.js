import localtunnel from 'localtunnel';
import qrcode from 'qrcode-terminal';

import fs from 'fs';

const PORT = 5173;


const MAX_RETRIES = 10;
let retryCount = 0;

console.log('Starting tunnel...');

async function startTunnel() {
    try {
        const response = await fetch('https://api.ipify.org?format=json');
        const data = await response.json();

        console.log(`\nYour IP (Password): ${data.ip}`);

        const tunnel = await localtunnel({ port: PORT });

        // Save URL to file for the agent to read
        fs.writeFileSync('public_url.txt', tunnel.url);

        console.log(`\nTunnel started at: ${tunnel.url}`);
        console.log('Scan the QR code below to view on mobile:\n');

        qrcode.generate(tunnel.url, { small: true });

        // Reset retry count on success
        retryCount = 0;

        tunnel.on('close', () => {
            console.log('Tunnel closed. Restarting...');
            setTimeout(startTunnel, 5000);
        });

        tunnel.on('error', (err) => {
            console.log('Tunnel error:', err);
            tunnel.close();
        });

    } catch (err) {
        console.error('Failed to create tunnel:', err);
        if (retryCount < MAX_RETRIES) {
            retryCount++;
            console.log(`Retrying in 5 seconds... (${retryCount}/${MAX_RETRIES})`);
            setTimeout(startTunnel, 5000);
        } else {
            console.log('Max retries reached. Exiting.');
        }
    }
}

startTunnel();
