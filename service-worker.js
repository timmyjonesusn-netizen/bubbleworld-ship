// Minimal app-shell cache so the ship opens fast and works full-screen
const CACHE = "bubble-ship-v1";
const CORE = [
  "./",
  "./index.html",
  "./manifest.webmanifest"
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // Only cache within this repo scope
  if (url.pathname.startsWith("/bubbleworld-ship/")) {
    e.respondWith(
      caches.match(e.request).then(res => res || fetch(e.request))
    );
  }
});
