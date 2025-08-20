// v1
const CACHE_NAME = "falowen-cache-v1";
const OFFLINE_URL = "/offline.html";
const PRECACHE = [OFFLINE_URL, "/static/icons/falowen-192.png", "/static/icons/falowen-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

// Pages: network-first, fall back to offline
self.addEventListener("fetch", (e) => {
  const r = e.request;
  if (r.mode === "navigate") {
    e.respondWith((async () => {
      try {
        const fresh = await fetch(r);
        const cache = await caches.open(CACHE_NAME);
        cache.put(r, fresh.clone());
        return fresh;
      } catch {
        const cached = await caches.match(r);
        return cached || caches.match(OFFLINE_URL);
      }
    })());
    return;
  }
  // Static: cache-first
  if (["style", "script", "image", "font"].includes(r.destination)) {
    e.respondWith(caches.match(r).then(hit => hit || fetch(r).then(resp => {
      caches.open(CACHE_NAME).then(c => c.put(r, resp.clone()));
      return resp;
    })));
  }
});
