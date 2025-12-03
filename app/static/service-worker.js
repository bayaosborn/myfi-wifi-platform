const CACHE_NAME = 'myfi-v2.2';

self.addEventListener('install', event => {
  console.log('[SW] Installing...');
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  console.log('[SW] Activating...');
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  // Network-first strategy (no caching yet)
  event.respondWith(fetch(event.request));
});