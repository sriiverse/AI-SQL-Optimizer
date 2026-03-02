#!/usr/bin/env node

const WebSocket = require('ws');
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

console.log("==========================================");
console.log("   🚀 QueryForge Local Agent (v1.0.0)    ");
console.log("==========================================");

rl.question('Enter a unique Client ID (e.g., your name): ', (clientId) => {
    rl.question('Enter Database Connection String (e.g., postgresql://localhost:5432/db): ', (dbString) => {

        console.log(`\n[Agent] Connecting to QueryForge Servers as client: ${clientId}...`);

        // Connect to the local FastAPI backend for testing (in prod this would be the Render URL)
        const wsUrl = `ws://localhost:8000/ws/agent/${clientId}`;
        const ws = new WebSocket(wsUrl);

        ws.on('open', () => {
            console.log(`[Agent] ✅ Connected securely to QueryForge Server.`);
            console.log(`[Agent] 🔒 Tunnel established to local DB: ${dbString.split('@')[1] || dbString}`);
            console.log(`[Agent] Waiting for execution commands from the browser...\n`);
        });

        ws.on('message', (data) => {
            try {
                const message = JSON.parse(data.toString());

                if (message.type === 'EXECUTE') {
                    console.log(`\n[Server Request] ⚡ Received Query to Execute:`);
                    console.log(`\x1b[36m${message.query}\x1b[0m`);

                    console.log(`[Agent] ⚙️ Simulating Execution on Local Database...`);

                    // Artificial delay to simulate real execution
                    setTimeout(() => {
                        const fakePlanResult = {
                            status: "success",
                            execution_time_ms: 42.5,
                            note: "This is a simulated response directly from the CLI Agent running on your laptop!"
                        };

                        console.log(`[Agent] ✅ Execution Complete. Sending results back to cloud...`);
                        ws.send(JSON.stringify(fakePlanResult));
                    }, 1500);
                }
            } catch (err) {
                console.error("[Agent] Error processing message:", err);
            }
        });

        ws.on('close', () => {
            console.log(`[Agent] ❌ Connection to QueryForge Server lost.`);
            process.exit(0);
        });

        ws.on('error', (err) => {
            console.error(`[Agent] WebSocket Error:`, err.message);
        });
    });
});
