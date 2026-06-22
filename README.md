# MeLi Local Delivery

Chrome extension. Forces the **"Origen del envío: Local"** filter on MercadoLibre
Argentina searches — only items that ship from **within Argentina** (local
delivery, no international/customs delays). **On by default** — flip it off from
the toolbar popup when you want to see everything (incl. international sellers).

## Install (unpacked)

1. Open `chrome://extensions`
2. Toggle **Developer mode** (top right) ON
3. Click **Load unpacked** → pick this folder (`~/projects/meli-local-delivery`)
4. Pin the truck icon to the toolbar

(After any code change, hit the **↻ reload** button on the extension card.)

## How it works

- On any `mercadolibre.com.ar` search/listado page, the content script finds
  MeLi's **own** "Local" filter link (under the *Origen del envío* group) and
  follows the URL MeLi itself built — so we never hardcode MeLi's (changing)
  filter encoding.
- If the filter is already applied (shown as a removable chip), or the toolbar
  toggle is OFF, it does nothing.
- A per-URL guard + an "already-redirected targets" set prevent redirect loops.

## Toggle

Click the toolbar icon → switch ON/OFF. Default = ON. Changing it reloads the
active MeLi tab so it takes effect immediately.

## Tests

`tests/` holds HTML fixtures (built from MeLi's real sidebar markup) that load
the actual `content.js` with a navigation seam (`window.__meliLdGo`) and a
stubbed `chrome.storage`. To run:

```
cd ~/projects/meli-local-delivery && python3 -m http.server 8099   # noport
# then open the fixtures and read window.__navTarget:
#   tests/fixture-unfiltered.html → __navTarget = the "Local" URL   (applies)
#   tests/fixture-applied.html    → __navTarget = undefined         (no loop)
#   tests/fixture-off.html        → __navTarget = undefined         (toggle off)
```

All three verified green via Playwright on 2026-06-22.

## If the filter ever stops applying

MeLi obfuscates class names, so this matches the visible text `Local`. If they
rename that option, update `LABELS` in `content.js`. (Grab the new label with a
console snippet on a MeLi search page — that's your browser, not an automated
fetch, so it's fine.)
