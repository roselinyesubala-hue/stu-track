// static/sw.js - Service Worker for Push Notifications

self.addEventListener('push', function (event) {
    console.log('[Service Worker] Push Received.');
    console.log(`[Service Worker] Push had this data: "${event.data.text()}"`);

    let data = { title: 'New Notification', body: 'You have a new update from StuTrack.' };
    try {
        if (event.data) {
            data = event.data.json();
        }
    } catch (e) {
        data.body = event.data.text();
    }

    const title = data.title;
    const options = {
        body: data.body,
        icon: '/static/icons/notification-icon.png', // Ensure this exists or use a generic one
        badge: '/static/icons/badge.png',
        data: data.url || '/'
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function (event) {
    console.log('[Service Worker] Notification click Received.');

    event.notification.close();

    event.waitUntil(
        clients.openWindow(event.notification.data || '/')
    );
});
