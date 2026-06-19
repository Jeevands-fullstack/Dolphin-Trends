// Dolphin Trends PWA Service Worker - FIXED
const STATIC_CACHE = 'dolphin-static-v4';
const API_CACHE = 'dolphin-api-v4';

// ✅ Only files that ACTUALLY exist
const staticUrlsToCache = [
  '/',
  '/index.html',
  '/dolphin.jpg',
  '/manifest.json',
  '/favicon.ico'
];

// Install - Only cache files that exist
self.addEventListener('install', event => {
  console.log('✅ Service Worker installing');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        // ✅ Add files one by one, skip if missing
        return Promise.all(
          staticUrlsToCache.map(url => {
            return fetch(url)
              .then(response => {
                if (response.ok) {
                  return cache.put(url, response);
                }
                console.log(`⚠️ Skipped (not found): ${url}`);
                return null;
              })
              .catch(err => {
                console.log(`⚠️ Skipped (error): ${url}`);
                return null;
              });
          })
        );
      })
      .then(() => self.skipWaiting())
  );
});

// Activate - Clean old caches
self.addEventListener('activate', event => {
  console.log('✅ Service Worker activated');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== STATIC_CACHE && cacheName !== API_CACHE) {
            console.log('🗑️ Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch - Cache First for static, Network First for API
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // ✅ Skip caching for Vercel internal files
  if (url.host.includes('vercel') && url.pathname.includes('main.')) {
    return;  // Let browser handle Vercel chunks directly
  }

  // ✅ API calls - Network First, Cache Fallback
  if (url.pathname.startsWith('/products') || 
      url.pathname.startsWith('/bookings') ||
      url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          if (response && response.status === 200) {
            const responseClone = response.clone();
            caches.open(API_CACHE).then(cache => {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          return caches.match(event.request).then(cachedResponse => {
            if (cachedResponse) {
              return cachedResponse;
            }
            if (url.pathname.startsWith('/products')) {
              return new Response(JSON.stringify([]), {
                headers: { 'Content-Type': 'application/json' }
              });
            }
            return new Response(JSON.stringify({error: 'Offline'}), {
              status: 503,
              headers: { 'Content-Type': 'application/json' }
            });
          });
        })
    );
    return;
  }

  // ✅ Static files - Cache First
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request)
          .then(fetchResponse => {
            if (!fetchResponse || fetchResponse.status !== 200) {
              return fetchResponse;
            }
            const responseToCache = fetchResponse.clone();
            caches.open(STATIC_CACHE)
              .then(cache => cache.put(event.request, responseToCache));
            return fetchResponse;
          })
          .catch(() => {
            if (event.request.destination === 'document') {
              return caches.match('/');
            }
          });
      })
  );
});
