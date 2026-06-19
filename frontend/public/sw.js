// Dolphin Trends PWA Service Worker - v6 (Force Refresh)
const CACHE_VERSION = 'v6';
const STATIC_CACHE = `dolphin-static-${CACHE_VERSION}`;
const API_CACHE = `dolphin-api-${CACHE_VERSION}`;

// Don't pre-cache anything - cache on demand only
const ESSENTIAL_FILES = [
  '/'
];

// Install - Skip pre-caching (avoid 404 errors)
self.addEventListener('install', event => {
  console.log(`✅ SW ${CACHE_VERSION} installing`);
  self.skipWaiting();  // Force activate immediately
});

// Activate - DELETE all old caches
self.addEventListener('activate', event => {
  console.log(`✅ SW ${CACHE_VERSION} activated - clearing old caches`);
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          // Delete all old caches
          if (!cache.includes(CACHE_VERSION)) {
            console.log(`🗑️ Deleting old cache: ${cache}`);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch - Network First (always get fresh from server)
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Skip Vercel internal build files (let browser handle directly)
  if (url.host.includes('vercel') && 
      (url.pathname.includes('/main.') || 
       url.pathname.includes('.css') ||
       url.pathname.includes('.js'))) {
    return; // Let browser handle - no caching
  }

  // API requests - Network First, Cache Fallback
  if (url.pathname.startsWith('/products') || 
      url.pathname.startsWith('/bookings') ||
      url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Cache fresh response
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(API_CACHE).then(cache => {
              cache.put(event.request, clone);
            });
          }
          return response;
        })
        .catch(() => {
          // Offline - return from cache
          return caches.match(event.request).then(cached => {
            if (cached) return cached;
            
            // Fallback for /products
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

  // Static files - Network First (no cache for now)
  event.respondWith(
    fetch(event.request)
      .catch(() => caches.match(event.request))
  );
});
