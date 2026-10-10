#!/usr/bin/env node

const WebSocket = require('ws');
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

console.log("==========================================");
console.log("   QueryForge Local Agent (simulated)     ");
console.log("==========================================");
console.log("This agent opens a WebSocket and runs a timer.");
console.log("It does not connect to a database, execute SQL, run EXPLAIN, or measure database time.");
console.log("No login command is implemented.\n");

rl.question('Enter a client id (any label; this is not a login): ', (clientId) => {
    console.log(`\n[Agent] Opening a WebSocket as ${clientId}...`);
    console.log("[Agent] The server must have AGENT_ENABLED set. That switch is not authentication.");

    // Local backend. The agent does not use a database URL.
    const wsUrl = `ws://localhost:8000/ws/agent/${clientId}`;
    const ws = new WebSocket(wsUrl);

    ws.on('open', () => {
        console.log("[Agent] WebSocket open. This connection is not authenticated.");
        console.log("[Agent] Waiting for messages. Incoming queries are not executed.\n");
    });

    ws.on('message', (data) => {
        try {
            const message = JSON.parse(data.toString());

            if (message.type === 'EXECUTE') {
                console.log("\n[Server Request] Received a query. It will not be executed:");
                console.log(`\x1b[36m${message.query}\x1b[0m`);
                console.log("[Agent] Starting a simulated timer. No database connection is opened.");

                const startedAt = Date.now();
                const simulatedDelayMs = 50;

                setTimeout(() => {
                    const elapsedMs = Date.now() - startedAt;
                    const executionResult = {
                        type: "EXECUTION_RESULT",
                        execution_time_ms: elapsedMs,
                        note: "Simulated timer only. This agent did not connect to a database or execute the query."
                    };

                    console.log(`[Agent] Simulated timer finished after ${elapsedMs}ms. No query was executed.`);
                    ws.send(JSON.stringify(executionResult));
                }, simulatedDelayMs);
            }
        } catch (err) {
            console.error("[Agent] Error processing message:", err);
        }
    });

    ws.on('close', () => {
        console.log("[Agent] WebSocket closed.");
        process.exit(0);
    });

    ws.on('error', (err) => {
        console.error("[Agent] WebSocket error:", err.message);
    });
});
