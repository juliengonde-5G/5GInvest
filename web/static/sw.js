/**
 * 5GInvest - Service Worker
 * Gère le cache offline et les notifications push.
 */

const CACHE_NAME = '5ginvest-v2';
const ASSETS_TO_CACHE = [
  '/',
  '/static/index.html',
  '/static/app.js',
  '/static/style.css',
  '/manifest.json',
];

// Installation : mise en cache des assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activation : nettoyage des anciens caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) => {
      return Promise.all(
        names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n))
      );
    })
  );
  self.clients.claim();
});

// Fetch : réseau d'abord, cache en fallback
self.addEventListener('fetch', (event) => {
  // Ne pas cacher les appels API
  if (event.request.url.includes('/api/')) {
    event.respondWith(fetch(event.request));
    return;
  }
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

// Push notification reçue
self.addEventListener('push', (event) => {
  let data = { title: '5GInvest', body: 'Nouvelle alerte', data: {} };

  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: '/static/icon-192.png',
    badge: '/static/icon-192.png',
    tag: data.tag || '5ginvest',
    data: data.data || {},
    vibrate: [200, 100, 200],
    requireInteraction: data.urgency === 'high',
    actions: [],
  };

  // Actions contextuelles selon le type d'alerte
  if (data.data && data.data.action === 'SELL') {
    options.actions = [
      { action: 'open', title: 'Voir détails' },
      { action: 'dismiss', title: 'Plus tard' },
    ];
    options.requireInteraction = true;
  }

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Clic sur la notification
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const url = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Si une fenêtre est déjà ouverte, la focus
      for (const client of clientList) {
        if (client.url.includes(self.location.origin)) {
          client.navigate(url);
          return client.focus();
        }
      }
      // Sinon ouvrir une nouvelle fenêtre
      return clients.openWindow(url);
    })
  );
});
