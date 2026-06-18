// Dolphin Trends PWA Service Worker - Enhanced
const CACHE_NAME = 'dolphin-trends-v2';
const STATIC_CACHE = 'dolphin-static-v2';
const API_CACHE = 'dolphin-api-v2';

// Static files (HTML, CSS, JS, Images)
const staticUrlsToCache = [
  '/',
  '/index.html',
  '/dolphin.jpg',
  '/manifest.json',
  '/logo-preview.jpg'
];

// Install Service Worker
self.addEventListener('install', event => {
  console.log('✅ Service Worker installing');
  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then(cache => {
        console.log('✅ Static cache opened');
        return cache.addAll(staticUrlsToCache);
      }),
      caches.open(API_CACHE).then(cache => {
        console.log('✅ API cache opened');
        return cache.add('/');
      })
    ]).then(() => self.skipWaiting())
  );
});

// Activate
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

// Fetch Event - Network First with Cache Fallback for API
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // ✅ API calls (products, bookings) - Network First
  if (url.pathname.startsWith('/products') || 
      url.pathname.startsWith('/bookings') ||
      url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // ✅ Online - Cache ನಲ್ಲಿ save ಮಾಡಿ
          if (response && response.status === 200) {
            const responseClone = response.clone();
            caches.open(API_CACHE).then(cache => {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // ✅ Offline - Cache ನಿಂದ ತೋರಿಸಿ
          return caches.match(event.request).then(cachedResponse => {
            if (cachedResponse) {
              console.log('📦 Serving from cache:', event.request.url);
              return cachedResponse;
            }
            // Empty array fallback for /products
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
        return response || fetch(event.request).then(fetchResponse => {
          if (!fetchResponse || fetchResponse.status !== 200 || fetchResponse.type !== 'basic') {
            return fetchResponse;
          }
          const responseToCache = fetchResponse.clone();
          caches.open(STATIC_CACHE)
            .then(cache => cache.put(event.request, responseToCache));
          return fetchResponse;
        });
      })
      .catch(() => {
        // Offline fallback
        if (event.request.destination === 'document') {
          return caches.match('/');
        }
      })
  );
});
