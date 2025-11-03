const CACHE_NAME = 'myfi-v2-cache';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/css/modal.css',
  '/static/js/main.js',
  //'/search',
  '/static/css/search/search.css',
  //'/static/js/search/search.js',
  '/static/logo.svg'
];

// Install service worker and cache assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('✅ Cache opened');
        return cache.addAll(urlsToCache);
      })
  );
  self.skipWaiting();
});

// Fetch from cache first, then network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});

// Clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

/*Push Notifications*/

self.addEventListener('push', function(event) {
    if (!event.data) {
        return;
    }
    
    const data = event.data.json();
    
    const options = {
        body: data.body,
        icon: data.icon || '/static/images/logo.png',
        badge: data.badge || '/static/images/badge.png',
        data: {
            url: data.url || '/'
        },
        timestamp: Date.parse(data.timestamp) || Date.now(),
        requireInteraction: false
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});