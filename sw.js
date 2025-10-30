// sw.js — Timmy Time Rock Cache
const CACHE = 'timmy-rock-v1';
const ASSETS = [
  './',
  './index.html',
  './offline.html'
];

self.addEventListener('install', e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(self.skipWaiting()));
});
self.addEventListener('activate', e=>{
  e.waitUntil(
    caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))
      .then(()=>self.clients.claim())
  );
});
self.addEventListener('fetch', e=>{
  const req = e.request;
  // HTML: network first, fallback to cache, then offline page
  if (req.headers.get('accept')?.includes('text/html')) {
    e.respondWith(
      fetch(req).then(res=>{
        const copy = res.clone();
        caches.open(CACHE).then(c=>c.put(req, copy));
        return res;
      }).catch(()=>caches.match(req).then(r=>r || caches.match('./offline.html')))
    );
    return;
  }
  // Others: cache first, network fallback
  e.respondWith(
    caches.match(req).then(r=> r || fetch(req).then(res=>{
      const copy = res.clone(); caches.open(CACHE).then(c=>c.put(req, copy)); return res;
    }))
  );
});
