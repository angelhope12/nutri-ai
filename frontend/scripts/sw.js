const CACHE_NAME = 'nutri-ai-v4-profile';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/assets/style.css',
  '/assets/nutrition.css',
  '/assets/interior.css',
  '/assets/food-bowl.svg',
  '/welcome.html',
  '/scripts/welcome.js',
  '/scripts/entry.js',
  '/scripts/app.js',
    '/scripts/measurements.js',
  '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      // return cached version or fetch from network
      return response || fetch(event.request);
    })
  );
});

// --- WEB PUSH NOTIFICATION LISTENERS ---
self.addEventListener('push', event => {
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { body: event.data.text() };
    }
  }

  const title = data.title || 'NutriAI Daily Reminder';
  const options = {
    body: data.body || 'Time to check your meals!',
    icon: '/assets/icons/icon-192.png',
    badge: '/assets/icons/icon-192.png',
    data: {
      url: data.url || '/index.html'
    }
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      const targetUrl = event.notification.data.url;
      // Check if there is already a window open with this app
      for (const client of clientList) {
        // Match base domain or relative url
        if ('focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
