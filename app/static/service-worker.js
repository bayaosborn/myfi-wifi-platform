/**
 * MyFi Service Worker
 * Handles offline caching and PWA functionality
 */

const CACHE_NAME = 'myfi-v1.0.0';
const RUNTIME_CACHE = 'myfi-runtime';

// Files to cache immediately on install
const PRECACHE_URLS = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/js/logic.js',
  '/static/images/icons/icon-192.jpg',
  '/static/images/icons/icon-512.jpg',
  '/offline.html' // Fallback page
];

// Install event - cache core assets
self.addEventListener('install', (event) => {
  console.log('⚙️ Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('📦 Service Worker: Caching core assets');
        return cache.addAll(PRECACHE_URLS);
      })
      .then(() => {
        console.log('✅ Service Worker: Installed successfully');
        return self.skipWaiting(); // Activate immediately
      })
      .catch((error) => {
        console.error('❌ Service Worker: Install failed', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('🔄 Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => {
              // Delete old caches
              return name !== CACHE_NAME && name !== RUNTIME_CACHE;
            })
            .map((name) => {
              console.log('🗑️ Service Worker: Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => {
        console.log('✅ Service Worker: Activated');
        return self.clients.claim(); // Take control immediately
      })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }
  
  // Skip API calls from caching (always go to network)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .catch(() => {
          // API failed, return error response
          return new Response(
            JSON.stringify({ error: 'Offline', offline: true }),
            { 
              headers: { 'Content-Type': 'application/json' },
              status: 503
            }
          );
        })
    );
    return;
  }
  
  // For everything else: Cache-first strategy
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          console.log('📦 Serving from cache:', request.url);
          
          // Return cached version immediately
          // But also fetch fresh version in background
          event.waitUntil(
            fetch(request)
              .then((freshResponse) => {
                return caches.open(RUNTIME_CACHE)
                  .then((cache) => {
                    cache.put(request, freshResponse.clone());
                    return freshResponse;
                  });
              })
              .catch(() => {
                // Network failed, but we have cache
              })
          );
          
          return cachedResponse;
        }
        
        // Not in cache, fetch from network
        console.log('🌐 Fetching from network:', request.url);
        return fetch(request)
          .then((response) => {
            // Don't cache if not successful
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Clone response (can only be consumed once)
            const responseToCache = response.clone();
            
            // Cache for next time
            caches.open(RUNTIME_CACHE)
              .then((cache) => {
                cache.put(request, responseToCache);
              });
            
            return response;
          })
          .catch((error) => {
            console.error('❌ Fetch failed:', error);
            
            // Return offline page for HTML requests
            if (request.headers.get('Accept').includes('text/html')) {
              return caches.match('/offline.html');
            }
            
            // For other requests, return empty response
            return new Response('Offline', {
              status: 503,
              statusText: 'Service Unavailable'
            });
          });
      })
  );
});

// Background sync (for future implementation)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-contacts') {
    console.log('🔄 Background sync: contacts');
    event.waitUntil(syncContacts());
  }
});

// Push notifications (for future implementation)
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  
  const options = {
    body: data.body || 'New notification',
    icon: '/static/images/icons/icon-192.jpg',
    badge: '/static/images/icons/icon-192.jpg',
    vibrate: [200, 100, 200],
    data: data
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'MyFi', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/')
  );
});

// Helper: Sync contacts (placeholder for future)
async function syncContacts() {
  try {
    const response = await fetch('/api/contacts/sync', {
      method: 'POST'
    });
    return response.json();
  } catch (error) {
    console.error('Sync failed:', error);
  }
}

// Message handler (for communication with app)
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(RUNTIME_CACHE)
        .then((cache) => cache.addAll(event.data.urls))
    );
  }
});

console.log('🚀 Service Worker: Loaded');