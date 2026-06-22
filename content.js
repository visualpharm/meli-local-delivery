// MeLi Local Delivery — content script.
//
// Goal: on MercadoLibre Argentina search/listado pages, force the
// "Origen del envío → Local" filter ON by default — i.e. only items that ship
// from within Argentina (local delivery, no international/customs delays).
//
// Hard constraint: we never hardcode MeLi's filter URL encoding (they change
// it). Instead we locate MeLi's OWN sidebar filter link labeled "Local" and
// follow the URL MeLi itself built. If the filter is already applied, or the
// toolbar toggle is OFF, we do nothing.

(() => {
  "use strict";

  const STORAGE_KEY = "localDeliveryEnabled"; // default true
  const ACTED_KEY = "__meli_ld_acted_for__"; // per-URL guard
  const TARGETS_KEY = "__meli_ld_targets__"; // URLs we've already redirected TO

  // The "Origen del envío" option that means domestic shipping.
  const LABELS = ["local"];

  const norm = (s) => (s || "").replace(/\s+/g, " ").trim().toLowerCase();

  // Navigation seam: overridable in tests, real redirect in production.
  const go =
    typeof window.__meliLdGo === "function"
      ? window.__meliLdGo
      : (u) => {
          location.href = u;
        };

  function visitedTargets() {
    try {
      return new Set(JSON.parse(sessionStorage.getItem(TARGETS_KEY) || "[]"));
    } catch {
      return new Set();
    }
  }
  function rememberTarget(u) {
    const s = visitedTargets();
    s.add(u);
    sessionStorage.setItem(TARGETS_KEY, JSON.stringify([...s]));
  }

  // Already applied? MeLi shows applied filters as a removable chip whose
  // aria-label reads e.g. "Quitar el filtro Local".
  function alreadyFiltered() {
    for (const el of document.querySelectorAll("[aria-label]")) {
      const aria = norm(el.getAttribute("aria-label"));
      const isRemove =
        aria.includes("quitar") || aria.includes("eliminar") || aria.includes("sacar");
      if (isRemove && LABELS.some((l) => aria.includes(l))) return true;
    }
    return false;
  }

  // Find the sidebar "Local" filter link (an <a> whose visible text is "Local").
  function findFilterLink() {
    for (const a of document.querySelectorAll("a[href]")) {
      if (!LABELS.includes(norm(a.textContent))) continue;

      const href = a.getAttribute("href") || "";
      if (!href || href.startsWith("#") || href.startsWith("javascript:")) continue;

      const low = href.toLowerCase();
      if (low.includes("ayuda") || low.includes("/help") || low.includes("hub")) continue;
      if (!low.includes("mercadolibre.com") && !href.startsWith("/")) continue;

      // Skip remove-chip anchors (these REMOVE an applied filter).
      const aria = norm(a.getAttribute("aria-label"));
      if (aria.includes("quitar") || aria.includes("eliminar") || aria.includes("sacar")) continue;
      if (a.closest('[class*="applied"], [class*="chips"], [class*="breadcrumb"]')) continue;

      return a;
    }
    return null;
  }

  function apply() {
    chrome.storage.sync.get({ [STORAGE_KEY]: true }, (cfg) => {
      if (cfg[STORAGE_KEY] === false) return; // explicitly turned OFF
      if (sessionStorage.getItem(ACTED_KEY) === location.href) return; // acted here already
      if (alreadyFiltered()) return;

      const link = findFilterLink();
      if (!link) return;

      const target = link.href; // absolute, browser-resolved
      if (!target || target === location.href) return;
      if (visitedTargets().has(target)) return; // never re-visit a URL we produced

      sessionStorage.setItem(ACTED_KEY, location.href);
      rememberTarget(target);
      go(target);
    });
  }

  // MeLi loads the filters sidebar asynchronously, so poll briefly.
  let tries = 0;
  const timer = setInterval(() => {
    apply();
    if (++tries >= 20) clearInterval(timer); // ~10s then give up
  }, 500);

  if (document.readyState === "complete" || document.readyState === "interactive") {
    apply();
  } else {
    document.addEventListener("DOMContentLoaded", apply);
  }
})();
