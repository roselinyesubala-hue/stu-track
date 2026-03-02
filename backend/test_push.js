const mysql = require('mysql2/promise');
const webpush = require('web-push');

const VAPID_PUBLIC_KEY = 'BM_ColqRevtvNPpBxRqrXk225U9HNakBwOHfpn19iYqMpktYgRnAEcl04noWb7IzvJhKhKvWZFmV83HIpU_KawM';
const VAPID_PRIVATE_KEY = 'yk-ZbXk1qj0AkA3Im-ZwqFrYDXtUrFP2XvQ6iDeaQVA';

webpush.setVapidDetails(
    'mailto:sju.stutrack@gmail.com',
    VAPID_PUBLIC_KEY,
    VAPID_PRIVATE_KEY
);

async function testPush() {
    console.log("Connecting to MySQL Database...");
    try {
        const connection = await mysql.createConnection({
            host: 'localhost',
            user: 'root',
            password: 'Rose@1979',
            database: 'stu_track'
        });

        console.log("Connected! Fetching subscriptions...");
        const [rows] = await connection.execute('SELECT * FROM push_subscription');

        if (rows.length === 0) {
            console.log("CRITICAL ERROR: No subscriptions found in the database. The frontend is NOT successfully registering with the backend.");
            process.exit(0);
        }

        console.log(`Found ${rows.length} subscriptions. Testing the first one...`);
        const sub = rows[rows.length - 1]; // Get latest

        const pushSubscription = {
            endpoint: sub.endpoint,
            keys: {
                auth: sub.auth,
                p256dh: sub.p256dh
            }
        };

        const payload = JSON.stringify({
            title: 'Diagnostic Test',
            body: 'Direct from Node Web-Push',
            url: '/'
        });

        try {
            await webpush.sendNotification(pushSubscription, payload);
            console.log("SUCCESS! Push notification delivered to the endpoint.");
        } catch (error) {
            console.error("FAIL: Web-Push library crashed or endpoint rejected the message.", error);
        }

        await connection.end();
    } catch (e) {
        console.error("Database connection failed:", e);
    }
}

testPush();
