/**
 * Service Worker for Home Assistant AI PWA
 * Provides offline functionality and caching
 */

const CACHE_NAME = 'home-assistant-ai-v1.0.0';
const STATIC_CACHE_NAME = 'home-assistant-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'home-assistant-dynamic-v1.0.0';

// Files to cache immediately
const STATIC_FILES = [
    '/',
    '/static/enhanced-app.js',
    '/static/manifest.json',
    '/static/style.css'
];

// API endpoints that can be cached for short periods
const CACHEABLE_APIS = [
    '/status',
    '/devices',
    '/scenarios',
    '/analytics/energy',
    '/analytics/devices',
    '/voice/status'
];

// Install event - cache static files
self.addEventListener('install', event => {
    console.log('Service Worker installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then(cache => {
                console.log('Caching static files');
                return cache.addAll(STATIC_FILES);
            })
            .then(() => {
                console.log('Static files cached');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('Failed to cache static files:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== STATIC_CACHE_NAME && 
                            cacheName !== DYNAMIC_CACHE_NAME &&
                            cacheName !== CACHE_NAME) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Old caches cleaned up');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve cached content or fetch from network
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Handle different types of requests
    if (isStaticFile(url.pathname)) {
        // Static files - cache first, then network
        event.respondWith(handleStaticFile(request));
    } else if (isCacheableAPI(url.pathname)) {
        // API endpoints - network first, then cache
        event.respondWith(handleCacheableAPI(request));
    } else if (isStreamingAPI(url.pathname)) {
        // Streaming APIs - network only
        event.respondWith(handleStreamingAPI(request));
    } else {
        // Other requests - network first
        event.respondWith(handleNetworkFirst(request));
    }
});

// Check if the request is for a static file
function isStaticFile(pathname) {
    return pathname.startsWith('/static/') || 
           pathname === '/' ||
           pathname.endsWith('.html') ||
           pathname.endsWith('.css') ||
           pathname.endsWith('.js') ||
           pathname.endsWith('.png') ||
           pathname.endsWith('.jpg') ||
           pathname.endsWith('.svg') ||
           pathname.endsWith('.ico');
}

// Check if the API endpoint can be cached
function isCacheableAPI(pathname) {
    return CACHEABLE_APIS.some(api => pathname.startsWith(api));
}

// Check if the API is streaming (should not be cached)
function isStreamingAPI(pathname) {
    return pathname.includes('/voice/listen') ||
           pathname.includes('/voice/speak') ||
           pathname.includes('/spotify/callback') ||
           pathname.includes('/wifi/connect');
}

// Handle static files with cache-first strategy
async function handleStaticFile(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
        
    } catch (error) {
        console.error('Failed to fetch static file:', error);
        
        // Try to return cached version as fallback
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page for HTML requests
        if (request.headers.get('accept').includes('text/html')) {
            return new Response(getOfflinePage(), {
                headers: { 'Content-Type': 'text/html' }
            });
        }
        
        return new Response('Offline', { status: 503 });
    }
}

// Handle cacheable APIs with network-first strategy (short TTL)
async function handleCacheableAPI(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE_NAME);
            
            // Clone the response and add a timestamp
            const responseToCache = networkResponse.clone();
            const response = await responseToCache.json();
            
            // Add cache metadata
            const cachedData = {
                data: response,
                timestamp: Date.now(),
                ttl: 30000 // 30 seconds TTL
            };
            
            await cache.put(request, new Response(JSON.stringify(cachedData), {
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'max-age=30'
                }
            }));
        }
        
        return networkResponse;
        
    } catch (error) {
        console.log('Network failed for API, trying cache:', request.url);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            const cachedData = await cachedResponse.json();
            
            // Check if cache is still valid
            if (cachedData.timestamp && 
                (Date.now() - cachedData.timestamp) < cachedData.ttl) {
                return new Response(JSON.stringify(cachedData.data), {
                    headers: { 'Content-Type': 'application/json' }
                });
            }
        }
        
        // Return error response for API requests
        return new Response(JSON.stringify({
            error: 'Service unavailable',
            offline: true
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Handle streaming APIs with network-only strategy
async function handleStreamingAPI(request) {
    try {
        return await fetch(request);
    } catch (error) {
        return new Response(JSON.stringify({
            error: 'Service unavailable',
            message: 'This feature requires an internet connection'
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Handle other requests with network-first strategy
async function handleNetworkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
        
    } catch (error) {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return new Response('Service unavailable', { status: 503 });
    }
}

// Generate offline page HTML
function getOfflinePage() {
    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Home Assistant AI - Offline</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: #f8fafc;
                    color: #1e293b;
                    text-align: center;
                    padding: 2rem;
                }
                .offline-icon {
                    font-size: 4rem;
                    margin-bottom: 1rem;
                }
                .offline-title {
                    font-size: 2rem;
                    font-weight: 700;
                    margin-bottom: 1rem;
                    color: #2563eb;
                }
                .offline-message {
                    font-size: 1.1rem;
                    margin-bottom: 2rem;
                    color: #64748b;
                    max-width: 500px;
                }
                .retry-button {
                    background: #2563eb;
                    color: white;
                    border: none;
                    padding: 1rem 2rem;
                    border-radius: 0.5rem;
                    font-size: 1rem;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                .retry-button:hover {
                    background: #1d4ed8;
                }
                .offline-features {
                    margin-top: 2rem;
                    padding: 1.5rem;
                    background: white;
                    border-radius: 0.5rem;
                    border: 1px solid #e2e8f0;
                    max-width: 400px;
                }
                .feature-item {
                    display: flex;
                    align-items: center;
                    margin: 0.5rem 0;
                    color: #64748b;
                }
                .feature-icon {
                    margin-right: 0.5rem;
                }
            </style>
        </head>
        <body>
            <div class="offline-icon">📱</div>
            <h1 class="offline-title">You're Offline</h1>
            <p class="offline-message">
                Home Assistant AI is currently offline. Some features may be limited, 
                but you can still access cached data and settings.
            </p>
            <button class="retry-button" onclick="window.location.reload()">
                Try Again
            </button>
            
            <div class="offline-features">
                <h3>Available Offline:</h3>
                <div class="feature-item">
                    <span class="feature-icon">✓</span>
                    View cached device status
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✓</span>
                    Browse scenarios
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✓</span>
                    View analytics data
                </div>
                <div class="feature-item">
                    <span class="feature-icon">✓</span>
                    Access settings
                </div>
            </div>
        </body>
        </html>
    `;
}

// Handle background sync (if supported)
self.addEventListener('sync', event => {
    console.log('Background sync triggered:', event.tag);
    
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

// Background sync function
async function doBackgroundSync() {
    try {
        // Sync any pending data when connection is restored
        console.log('Performing background sync...');
        
        // Try to fetch latest device status
        await fetch('/status');
        await fetch('/devices');
        
        console.log('Background sync completed');
        
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

// Enhanced PWA features - notification handlers
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    const action = event.action || 'default';
    
    switch (action) {
        case 'open-devices':
            event.waitUntil(clients.openWindow('/?tab=devices'));
            break;
        case 'voice-control':
            event.waitUntil(clients.openWindow('/?action=voice'));
            break;
        case 'spotify-control':
            event.waitUntil(clients.openWindow('/?action=spotify'));
            break;
        case 'open-settings':
            event.waitUntil(clients.openWindow('/?tab=settings'));
            break;
        default:
            event.waitUntil(clients.openWindow('/'));
            break;
    }
});

// Enhanced message handling for PWA features
self.addEventListener('message', (event) => {
    const { type, data } = event.data || {};
    
    switch (type) {
        case 'SHOW_NOTIFICATION':
            self.registration.showNotification(data.title, data.options);
            break;
        case 'CACHE_UPDATE':
            event.waitUntil(updateStaticCache());
            break;
        case 'CLEAR_CACHE':
            event.waitUntil(clearAllCaches());
            break;
    }
});

// Update static cache on demand
async function updateStaticCache() {
    try {
        const cache = await caches.open(STATIC_CACHE_NAME);
        await cache.addAll(STATIC_FILES);
        console.log('Static cache updated successfully');
    } catch (error) {
        console.error('Cache update failed:', error);
    }
}

// Clear all caches
async function clearAllCaches() {
    try {
        const cacheNames = await caches.keys();
        await Promise.all(
            cacheNames.map(cacheName => caches.delete(cacheName))
        );
        console.log('All caches cleared successfully');
    } catch (error) {
        console.error('Cache clear failed:', error);
    }
}

// Handle push notifications (if implemented)
self.addEventListener('push', event => {
    if (!event.data) return;
    
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        vibrate: [100, 50, 100],
        data: data.data,
        actions: data.actions || []
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    const action = event.action;
    const data = event.notification.data;
    
    event.waitUntil(
        clients.openWindow(data.url || '/')
    );
});

// Log service worker messages
self.addEventListener('message', event => {
    console.log('Service Worker received message:', event.data);
    
    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data.type === 'CACHE_URLS') {
        event.waitUntil(
            caches.open(DYNAMIC_CACHE_NAME)
                .then(cache => cache.addAll(event.data.urls))
        );
    }
});

console.log('Service Worker loaded successfully');