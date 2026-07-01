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

  // TEMP DEBUG — remove once the blink is confirmed fixed on the real site.
  const _t0 = Date.now();
  const DBG = (...a) => console.log("[MeLiLD]", `+${Date.now() - _t0}ms`, ...a);
  DBG("script start", location.href);

  const STORAGE_KEY = "localDeliveryEnabled"; // default true
  const ACTED_KEY = "__meli_ld_acted_for__"; // per-URL guard
  const TARGETS_KEY = "__meli_ld_targets__"; // URLs we've already redirected TO

  // The "Origen del envío" option that means domestic shipping.
  const LABELS = ["local"];

  // Longest we'll hold the page hidden while deciding whether to redirect.
  // Bounded short so non-listing pages (product, cart, home...) where the
  // "Local" link will never appear aren't held blank for long.
  const HIDE_BUDGET_MS = 1500;

  const norm = (s) => (s || "").replace(/\s+/g, " ").trim().toLowerCase();

  // Navigation seam: overridable in tests, real redirect in production.
  const go =
    typeof window.__meliLdGo === "function"
      ? window.__meliLdGo
      : (u) => {
          location.href = u;
        };

  // Hide the page until we've decided whether to redirect. Without this,
  // the unfiltered (international-included) results paint first and THEN
  // the page reloads to the local-only URL — visible as a blink. Runs at
  // document_start so this style lands before MeLi paints anything.
  let hideStyle = null;
  function hide() {
    if (hideStyle) return;
    hideStyle = document.createElement("style");
    hideStyle.textContent = "html{visibility:hidden!important}";
    document.documentElement.appendChild(hideStyle);
  }
  function reveal() {
    if (hideStyle) {
      DBG("reveal()");
      hideStyle.remove();
      hideStyle = null;
    }
  }
  hide();
  DBG("hide()");
  setTimeout(() => {
    DBG("HIDE_BUDGET_MS timeout fired");
    reveal();
  }, HIDE_BUDGET_MS);
  window.addEventListener("pageshow", (e) => {
    if (e.persisted) reveal(); // bfcache restore — don't stay hidden
  });

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

  // Already applied? Two independent signals — either is enough. MeLi's own
  // "Local" link carries a URL hash confirming what it just applied (e.g.
  // "#applied_filter_name=Origen+del+envío&applied_value_name=Local"), which
  // survives the redirect and is far more reliable than scraping the sidebar,
  // where the removable-chip markup varies (real-site testing found the
  // chip's aria-label check alone left the arrival page falsely "unfiltered"
  // for the full poll window). Neither check hardcodes MeLi's filter IDs —
  // both read the human-readable labels MeLi puts there itself.
  function alreadyFiltered() {
    let hash = "";
    try {
      hash = norm(decodeURIComponent(location.hash.replace(/\+/g, " ")));
    } catch {
      hash = norm(location.hash);
    }
    if (hash.includes("applied_value_name=local") && hash.includes("origen del env")) return true;

    for (const el of document.querySelectorAll("[aria-label]")) {
      const aria = norm(el.getAttribute("aria-label"));
      const isRemove =
        aria.includes("quitar") || aria.includes("eliminar") || aria.includes("sacar") || aria.includes("remover");
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

      // Skip the option if it (or its aria-label/input sibling) marks itself as
      // the CURRENTLY SELECTED one — a selected facet's link toggles it OFF,
      // it doesn't apply it. Real-site testing found the arrival page's own
      // "Local" sidebar entry stays a plain, unflagged link with none of the
      // above remove-chip markers, so without this check we'd re-click it and
      // undo our own filter (loads filtered -> "removes" it -> re-applies -> loop).
      if (aria.includes("seleccion") || a.getAttribute("aria-current") === "true") continue;
      if (a.querySelector('input[checked], input[aria-checked="true"]')) continue;
      if (a.closest('[aria-selected="true"], [class*="selected" i], [class*="active" i]')) continue;

      return a;
    }
    return null;
  }

  // Stop the poll loop the moment we reach ANY terminal decision. Without
  // this, a poll 5-10s later could re-evaluate against a DOM/URL that MeLi's
  // own client-side JS mutated since (e.g. stripping the confirmation hash),
  // flip our verdict, and fire a second, unwanted redirect — the exact
  // "loads filtered, then switches off, then reloads again" loop.
  let timer = null;
  function stop() {
    if (timer) {
      clearInterval(timer);
      timer = null;
      DBG("stop polling");
    }
  }

  function apply() {
    chrome.storage.sync.get({ [STORAGE_KEY]: true }, (cfg) => {
      if (cfg[STORAGE_KEY] === false) return DBG("OFF") || reveal() || stop(); // explicitly turned OFF
      if (sessionStorage.getItem(ACTED_KEY) === location.href) return DBG("already acted") || reveal() || stop();
      if (alreadyFiltered()) return DBG("already filtered") || reveal() || stop();

      const link = findFilterLink();
      if (!link) return DBG("no link yet"); // sidebar not rendered yet — keep waiting, stay hidden

      const target = link.href; // absolute, browser-resolved
      if (!target || target === location.href) return DBG("target === self") || reveal() || stop();
      if (visitedTargets().has(target)) return DBG("already visited target", target) || reveal() || stop();

      DBG("REDIRECTING to", target);
      sessionStorage.setItem(ACTED_KEY, location.href);
      rememberTarget(target);
      stop();
      go(target); // navigating away — stay hidden, the next document hides itself too
    });
  }

  // MeLi loads the filters sidebar asynchronously, so poll briefly. The
  // interval is armed BEFORE the first apply() call so stop() always has a
  // live timer to clear — chrome.storage callbacks are genuinely async in
  // production, but test fixtures mock them synchronously, and a stop()
  // racing ahead of `timer`'s own assignment would silently no-op.
  let tries = 0;
  timer = setInterval(() => {
    apply();
    if (++tries >= 20) stop(); // ~10s then give up
  }, 500);
  apply();
})();
