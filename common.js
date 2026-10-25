(function () {
  "use strict";
  // Mobile navigation toggle
  document.querySelectorAll('[data-toggle="nav"]').forEach(b => b.addEventListener("click", () => {
    document.getElementById("nav").classList.toggle("open");
  }));
  // Confirmation prompts for important actions
  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-confirm]");
    if (!t) return;
    const form = t.closest("form");
    if (form && !form.checkValidity()) return;
    if (!confirm(t.dataset.confirm)) { e.preventDefault(); return; }
    if (form && t.type === "submit") {
      // Prevent accidental double submission
      setTimeout(() => { t.disabled = true; t.textContent = "Please wait…"; }, 0);
    }
  });
  // Online / offline indicator
  const ns = document.getElementById("netstatus");
  const upd = () => { if (ns) ns.hidden = navigator.onLine; };
  window.addEventListener("online", upd); window.addEventListener("offline", upd); upd();
  // Section-permission matrix: "All parts" clears specific ticks and vice versa
  document.querySelectorAll("[data-allfor]").forEach(all => {
    const id = all.dataset.allfor;
    const boxes = document.querySelectorAll('[data-member="' + id + '"]');
    const sync = () => boxes.forEach(b => { b.disabled = all.checked; });
    all.addEventListener("change", sync); sync();
  });
  // Offline support for the inspection form
  const secure = location.protocol === "https:" || location.hostname === "localhost" || location.hostname === "127.0.0.1";
  if ("serviceWorker" in navigator && secure && document.querySelector(".topbar .nav")) {
    navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => {});
  }
})();
