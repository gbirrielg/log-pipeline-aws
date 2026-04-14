require('dotenv').config();

// config
const API_ENDPOINT = process.env.API_ENDPOINT;
const NUM_LOGS = 10;

// value pools
const STATUSES = ['INFO', 'ERROR', 'SUCCESS'];
const SERVICES = ['auth_service', 'login_service', 'purchasing_service'];

// helpers
function getRandomElement(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

function getRandomLatency() {
    return Math.floor(Math.random() * (200 - 20 + 1)) + 20;
}

function generateLog() {
    return {
        service_id: getRandomElement(SERVICES),
        timestamp: new Date().toISOString(),
        status: getRandomElement(STATUSES),
        latency_ms: getRandomLatency()
    };
}

// ONE-BY-ONE SENDER
// Sends logs one by one, for small tests
async function sendLogs() {
    for (let i = 0; i < NUM_LOGS; i++) {
        const log = generateLog();

        try {
            const res = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(log)
            });

            console.log(`Sent log ${i + 1}:`, log, `Response: ${res.status}`);
        } catch (err) {
            console.error(`Error sending log ${i + 1}:`, err.message);
        }
    }
}

// BURST SENDER
// Sends all logs in a parallel burst mode
async function sendLogsBurst() {
    const requests = [];

    for (let i = 0; i < NUM_LOGS; i++) {
        const log = generateLog();

        requests.push(
            fetch(API_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(log)
            })
        );
    }

    const responses = await Promise.allSettled(requests);
    console.log(responses);
}


// run
sendLogs();
//sendLogsBurst();