// MeLi Local Delivery — content script.
//
// Goal: on MercadoLibre Argentina search/listado pages, force the
// "Origen del envío → Local" filter ON by default — only items that ship
// from within Argentina — WITHOUT ever blinking the page.
//
// No-blink strategy (v1.1):
//  1. From document_start, international (CBT) result cards are hidden BEFORE
//     first paint: a CSS :has() rule keyed on MeLi's own cross-border badge
//     (.poly-component__cbt), plus a MutationObserver fallback that tags cards
//     whose accessible text starts with "Internacional". The page paints once,
//     already local-only. The whole-page visibility:hidden of v1.0 (the white
//     flash) is gone.
//  2. In the background, locate MeLi's OWN sidebar filter link labeled "Local"
//     and fetch the URL MeLi itself built (same-origin, with cookies). Swap
//     the results grid, result count and pagination in place and
//     history.replaceState to the filtered URL. Counters, order and pages end
//     up exactly as if the user had clicked the filter — but nothing
//     navigates, so nothing flickers.
//  3. Only if the in-place swap is impossible (fetch failed, markup drifted)
//     fall back to location.replace() of the filtered URL. With no page-hide
//     and the internationals already hidden, Chrome's paint holding makes
//     that a soft transition, not a white flash.
//
// Hard constraint kept from v1.0: never hardcode MeLi's filter URL encoding
// (they change it) — always follow the URL MeLi itself built into the sidebar
// link. If the filter is already applied, or the toolbar toggle is OFF, do
// nothing.

(() => {
  "use strict";

  const STORAGE_KEY = "localDeliveryEnabled"; // default true
  const ACTED_KEY = "__meli_ld_acted_for__"; // per-URL guard
  const TARGETS_KEY = "__meli_ld_targets__"; // URLs we've already redirected TO
  const MIRROR_KEY = "__meli_ld_on__"; // sync-readable mirror of the toggle
  const ATTR = "data-meli-ld-intl"; // set on cards the observer classifies

  // The "Origen del envío" option that means domestic shipping.
  const LABELS = ["local"];

  // Diagnostic/testing state (isolated world: invisible to MeLi's own JS).
  const state = (window.__meliLdState = { hiddenCards: 0, swapped: false, reason: null });

  const norm = (s) => (s || "").replace(/\s+/g, " ").trim().toLowerCase();

  // Seams: overridable in test fixtures (same-world <script src>), inert in
  // production where the content script world is isolated from the page.
  const go =
    typeof window.__meliLdGo === "function"
      ? window.__meliLdGo
      : (u) => {
          location.replace(u);
        };
  const fetchText =
    typeof window.__meliLdFetch === "function"
      ? window.__meliLdFetch
      : (u) =>
          fetch(u, { credentials: "include" }).then((r) => {
            if (!r.ok) throw new Error("HTTP " + r.status);
            return r.text();
          });

  // ------------------------------------------------------------------ toggle
  // chrome.storage is async; to hide international cards BEFORE first paint we
  // need a synchronous read, so the last-known toggle value is mirrored into
  // localStorage. The popup reloads the tab on toggle, so the mirror is always
  // refreshed (below, in the storage callback) before the next page load.
  function mirrorSaysOn() {
    try {
      return localStorage.getItem(MIRROR_KEY) !== "0";
    } catch {
      return true;
    }
  }

  // --------------------------------------------------- pre-paint intl hiding
  // Primary: pure CSS on MeLi's own cross-border badge — applies the instant
  // each card parses, so an international card never reaches the screen.
  // Secondary: the observer tags cards whose visually-hidden a11y text starts
  // with "Internacional" (covers a badge-markup drift as long as the a11y
  // text survives).
  let style = null;
  let observer = null;

  function installHiding() {
    style = document.createElement("style");
    style.setAttribute("data-meli-ld", "1"); // detectable from the page world (tests/diagnostics)
    style.textContent =
      `li.ui-search-layout__item:has(.poly-component__cbt),` +
      `li.ui-search-layout__item[${ATTR}]{display:none!important}`;
    // With run_at document_start <html> already exists; the defer branch covers
    // environments that inject even earlier (CDP harness).
    if (document.documentElement) {
      document.documentElement.appendChild(style);
    } else {
      const rootWait = new MutationObserver(() => {
        if (!document.documentElement) return;
        rootWait.disconnect();
        if (style) document.documentElement.appendChild(style);
      });
      rootWait.observe(document, { childList: true });
    }

    const INTL_RX = /^\s*internacional\b/i;
    const classify = (el) => {
      if (!el.matches) return;
      const marks = el.matches(".poly-component__cbt, .andes-visually-hidden")
        ? [el]
        : el.querySelectorAll(".poly-component__cbt, .andes-visually-hidden");
      for (const m of marks) {
        if (!m.classList.contains("poly-component__cbt") && !INTL_RX.test(m.textContent || "")) continue;
        const li = m.closest("li.ui-search-layout__item");
        if (li && !li.hasAttribute(ATTR)) {
          li.setAttribute(ATTR, "");
          state.hiddenCards++;
        }
      }
    };
    observer = new MutationObserver((muts) => {
      for (const mu of muts) for (const n of mu.addedNodes) if (n.nodeType === 1) classify(n);
    });
    observer.observe(document, { childList: true, subtree: true });
  }

  function teardownHiding() {
    if (observer) observer.disconnect(), (observer = null);
    if (style) style.remove(), (style = null);
    for (const el of document.querySelectorAll(`[${ATTR}]`)) el.removeAttribute(ATTR);
  }

  if (mirrorSaysOn()) installHiding();

  // ------------------------------------------------------- filter detection
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
  // survives into the filtered page and is far more reliable than scraping
  // the sidebar, where the removable-chip markup varies. Neither check
  // hardcodes MeLi's filter IDs — both read the human-readable labels MeLi
  // puts there itself.
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

  // -------------------------------------------------------- in-place swap
  // Replace the results grid, count and pagination with the ones from the
  // filtered page MeLi served. Everything else (header, sidebar) stays — the
  // sidebar still offers MeLi's own filters, whose links now simply navigate
  // to already-filtered pages.
  function swapDocument(html, targetUrl) {
    const doc = new DOMParser().parseFromString(html, "text/html");
    const newOl = doc.querySelector('ol[class*="ui-search-layout"]');
    const liveOl = document.querySelector('ol[class*="ui-search-layout"]');
    if (!newOl || !liveOl) return false;
    liveOl.replaceWith(document.adoptNode(newOl));

    const newQty = doc.querySelector('[class*="quantity-results"]');
    const liveQty = document.querySelector('[class*="quantity-results"]');
    if (newQty && liveQty) liveQty.textContent = newQty.textContent;

    const livePag = document.querySelector("ul.andes-pagination");
    const newPag = doc.querySelector("ul.andes-pagination");
    if (livePag) {
      if (newPag) livePag.replaceWith(document.adoptNode(newPag));
      else livePag.remove(); // filtered results fit one page
    }

    // Make reload/share/back land on the genuinely filtered URL (its hash also
    // marks the page as already-filtered for this script).
    try {
      history.replaceState(null, "", targetUrl);
    } catch {
      /* cross-origin in test fixtures */
    }
    return true;
  }

  // Stop the poll loop the moment we reach ANY terminal decision. Without
  // this, a poll 5-10s later could re-evaluate against a DOM/URL that MeLi's
  // own client-side JS mutated since (e.g. stripping the confirmation hash),
  // flip our verdict, and act a second, unwanted time.
  let timer = null;
  function stop() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }
  function done(reason) {
    state.reason = reason;
    stop();
  }

  let armed = false; // storage read confirmed the toggle is ON
  let acted = false;

  function fallbackGo(target) {
    if (visitedTargets().has(target)) return done("already visited target");
    rememberTarget(target);
    done("fallback navigation");
    go(target);
  }

  function apply() {
    if (!armed || acted) return;
    if (sessionStorage.getItem(ACTED_KEY) === location.href) return done("already acted");
    if (alreadyFiltered()) return done("already filtered");

    const link = findFilterLink();
    if (!link) return; // sidebar not rendered yet — keep polling

    const target = link.href; // absolute, browser-resolved
    if (!target || target === location.href) return done("target === self");

    acted = true;
    sessionStorage.setItem(ACTED_KEY, location.href);
    stop();
    fetchText(target)
      .then((html) => {
        if (swapDocument(html, target)) {
          state.swapped = true;
          state.reason = "swapped";
        } else {
          fallbackGo(target);
        }
      })
      .catch(() => fallbackGo(target));
  }

  // MeLi loads the filters sidebar asynchronously, so poll briefly. The
  // interval is armed BEFORE the first apply() call so stop() always has a
  // live timer to clear — chrome.storage callbacks are genuinely async in
  // production, but test fixtures mock them synchronously, and a stop()
  // racing ahead of `timer`'s own assignment would silently no-op.
  let tries = 0;
  timer = setInterval(() => {
    apply();
    if (++tries >= 20) done("gave up waiting for sidebar"); // ~10s then give up
  }, 500);

  chrome.storage.sync.get({ [STORAGE_KEY]: true }, (cfg) => {
    const on = cfg[STORAGE_KEY] !== false;
    try {
      localStorage.setItem(MIRROR_KEY, on ? "1" : "0");
    } catch {
      /* storage may be unavailable */
    }
    if (!on) {
      teardownHiding();
      return done("OFF");
    }
    if (!style) installHiding(); // mirror said OFF but the toggle is ON again
    armed = true;
    apply();
  });
})();
