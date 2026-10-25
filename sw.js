/* Service worker: lets an inspector reopen the form page and keep entering data
 * when the network drops. Data entered offline is kept in the browser and sent
 * by form.js when the connection returns. */
const CACHE = "iti-portal-v2";
const SHELL = [
  "/static/inspections/app.css",
  "/static/inspections/common.js",
  "/static/inspections/form.js",
  "/static/inspections/icon.svg",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  // Inspection pages and the list of my inspections: network first, cached copy when offline.
  if (req.mode === "navigate" && (/^\/inspection\/\d+\/form\/$/.test(url.pathname) || url.pathname === "/my-inspections/")) {
    e.respondWith(
      fetch(req).then((resp) => {
        if (resp.ok && !resp.redirected) {
          const copy = resp.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return resp;
      }).catch(() => caches.match(req).then((r) => r || new Response(
        "<h1>Offline</h1><p>This page has not been opened on this device before. Connect to the internet and open the inspection once so it is available offline.</p>",
        { headers: { "Content-Type": "text/html" } })))
    );
    return;
  }
  // Static files: cache first.
  if (url.pathname.startsWith("/static/")) {
    e.respondWith(caches.match(req).then((r) => r || fetch(req).then((resp) => {
      const copy = resp.clone();
      caches.open(CACHE).then((c) => c.put(req, copy));
      return resp;
    })));
  }
});
