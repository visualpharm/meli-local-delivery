#!/usr/bin/env python3
"""Extension test harness on the sanctioned meli_verify browser path.

Reuses the meli-skill's PERSISTENT COOKIED Chrome profile (never a clean
browser — that trips MeLi's bot wall and gets Ivan's session blocked), real
Chrome headless=new, off-screen, ONE reused tab, homepage warmed as Referer.
Same etiquette as products/meli-skill/meli_verify.py; this file only adds
`--load-extension` so the MeLi Local Delivery extension under test runs.

Modes:
  recon  — load ONE unfiltered search, dump how international cards are marked
           (extension NOT loaded), plus container/count/pagination selectors.
  blink  — load the extension, navigate to an unfiltered search, screencast
           frames + poll visible international cards; report any white frame,
           any visible intl card, and whether the final listing is filtered.

Uses CDP port 9223 so it never fights meli_verify.py's own Chrome on 9222;
kills a stale profile-locked Chrome first if needed.
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

MELI_SKILL = Path.home() / "projects/openclaw-private/products/meli-skill"
sys.path.insert(0, str(MELI_SKILL))
import meli_verify  # noqa: E402  (profile dir, chrome path — the sanctioned setup)

CHROME = meli_verify.CHROME
PROFILE_DIR = meli_verify.PROFILE_DIR
HOME = "https://www.mercadolibre.com.ar/"
CDP_PORT = 9223
EXT_DIR = Path(__file__).resolve().parent.parent
SHOTS = Path("/private/tmp/claude-501/-Users-ivan-projects-meli-local-delivery/41280461-8042-41ce-be18-81a1bf5aa0cd/scratchpad/blink-frames")

SEARCH_URL = "https://listado.mercadolibre.com.ar/auriculares-inalambricos"
SEARCH_QUERY = "auriculares inalambricos"


def _cdp_up(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def _kill_profile_chrome() -> None:
    """The profile allows one Chrome at a time; stop meli_verify's idle instance."""
    subprocess.run(["pkill", "-f", str(PROFILE_DIR)], capture_output=True)
    time.sleep(1.5)


def launch_chrome(with_extension: bool) -> None:
    if _cdp_up(CDP_PORT):
        return
    _kill_profile_chrome()
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    args = [
        CHROME,
        f"--user-data-dir={PROFILE_DIR}",
        f"--remote-debugging-port={CDP_PORT}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-blink-features=AutomationControlled",
        "--lang=es-AR",
        "--window-size=1280,1800",
        "--window-position=-2400,-2400",  # off-screen: never steals focus
        "--headless=new",
    ]
    if with_extension:
        args += [
            f"--disable-extensions-except={EXT_DIR}",
            f"--load-extension={EXT_DIR}",
        ]
    args.append("about:blank")
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        if _cdp_up(CDP_PORT):
            return
        time.sleep(0.5)
    raise RuntimeError(f"Chrome did not expose CDP on :{CDP_PORT}")


def connect():
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    return pw, browser, page


def warm(page) -> None:
    page.goto(HOME, wait_until="domcontentloaded", timeout=35000)
    time.sleep(2.5)


RECON_JS = r"""
() => {
  const out = {};
  const ol = document.querySelector('ol[class*="ui-search-layout"]');
  out.container = ol ? { tag: ol.tagName, cls: ol.className, parentCls: ol.parentElement.className } : null;
  const cards = ol ? [...ol.querySelectorAll(':scope > li')] : [];
  out.cardCount = cards.length;
  out.cardCls = cards[0] ? cards[0].className : null;

  const intl = [], local = [];
  for (const c of cards) {
    const t = (c.textContent || '').toLowerCase();
    (t.includes('internacional') ? intl : local).push(c);
  }
  out.intlCount = intl.length; out.localCount = local.length;

  const markers = [];
  if (intl[0]) {
    for (const el of intl[0].querySelectorAll('*')) {
      const t = (el.textContent || '').toLowerCase();
      if (t.includes('internacional') &&
          ![...el.children].some(ch => (ch.textContent || '').toLowerCase().includes('internacional'))) {
        markers.push({ tag: el.tagName, cls: el.className, text: el.textContent.trim().slice(0, 120) });
      }
    }
    out.intlCardSample = intl[0].outerHTML.slice(0, 3500);
  }
  out.intlMarkers = markers;

  const side = [...document.querySelectorAll('aside section, aside div, section')]
    .filter(s => /origen del env/i.test(s.textContent || ''));
  const sec = side.length ? side[side.length - 1] : null;
  out.origenSection = sec ? sec.outerHTML.slice(0, 2500) : null;

  const qty = document.querySelector('[class*="quantity-results"]');
  out.qty = qty ? { cls: qty.className, text: qty.textContent.trim() } : null;
  const pag = document.querySelector('.andes-pagination, nav[class*="pagination"], ul[class*="pagination"]');
  out.pagination = pag ? { tag: pag.tagName, cls: String(pag.className).slice(0, 200), parentCls: String(pag.parentElement.className).slice(0,200) } : null;
  return out;
}
"""


def recon() -> None:
    launch_chrome(with_extension=False)
    pw, browser, page = connect()
    try:
        warm(page)
        page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=35000, referer=HOME)
        try:
            page.wait_for_selector('ol[class*="ui-search-layout"] li', timeout=15000)
        except Exception:
            print("WARN: no results grid; body starts:", page.evaluate("document.body.innerText.slice(0,300)"), file=sys.stderr)
        time.sleep(2)
        print(json.dumps(page.evaluate(RECON_JS), indent=2, ensure_ascii=False))
    finally:
        browser.close()
        pw.stop()


# Poll installed from a CDP Page.addScriptToEvaluateOnNewDocument so it starts
# at document_start, alongside the extension: samples visible intl cards + doc
# visibility over time.
POLL_INSTALL = r"""
(() => {
  window.__blinkSamples = [];
  const t0 = performance.now();
  const tick = () => {
    let intlVisible = 0, cards = 0;
    try {
      for (const li of document.querySelectorAll('ol[class*="ui-search-layout"] > li')) {
        cards++;
        const t = (li.textContent || '').toLowerCase();
        if (t.includes('internacional')) {
          const r = li.getBoundingClientRect();
          const cs = getComputedStyle(li);
          if (r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden') intlVisible++;
        }
      }
    } catch (e) {}
    const htmlHidden = document.documentElement &&
      getComputedStyle(document.documentElement).visibility === 'hidden';
    window.__blinkSamples.push({
      t: Math.round(performance.now() - t0),
      cards, intlVisible, htmlHidden,
      url: location.pathname.slice(0, 60),
    });
  };
  setInterval(tick, 80);
})();
"""


def launch_chrome_headful() -> None:
    """Headful (off-screen) launch — headless=new trips MeLi's wall on this profile."""
    if _cdp_up(CDP_PORT):
        return
    _kill_profile_chrome()
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    args = [
        CHROME,
        f"--user-data-dir={PROFILE_DIR}",
        f"--remote-debugging-port={CDP_PORT}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-blink-features=AutomationControlled",
        "--lang=es-AR",
        "--window-size=1280,1800",
        "--window-position=-2400,-2400",  # off-screen: never steals focus
        "about:blank",
    ]
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        if _cdp_up(CDP_PORT):
            return
        time.sleep(0.5)
    raise RuntimeError(f"Chrome did not expose CDP on :{CDP_PORT}")


def blink() -> None:
    """No-blink verification on the real site.

    Chrome 137+ stable removed --load-extension, so the extension's content.js
    SOURCE is injected at document_start via CDP (with a chrome.storage stub) —
    same code, same timing, same rendering path as the packaged extension.
    """
    launch_chrome_headful()
    pw, browser, page = connect()
    SHOTS.mkdir(parents=True, exist_ok=True)
    for old in SHOTS.glob("*.png"):
        old.unlink()
    frames: list[tuple[int, bytes]] = []
    try:
        warm(page)
        content_js = (EXT_DIR / "content.js").read_text()
        # Defer until <html> exists — the moment run_at:document_start fires
        # for a real content script (CDP injection runs earlier than that).
        inject = (
            "(() => { if (!window.chrome) window.chrome = {};"
            " if (!window.chrome.storage) window.chrome.storage ="
            " { sync: { get: (d, cb) => cb(d) } }; })();\n"
            "const __meliLdRun = () => {\n" + content_js + "\n};\n"
            "if (document.documentElement) __meliLdRun();\n"
            "else { const o = new MutationObserver(() => { if (document.documentElement) {"
            " o.disconnect(); __meliLdRun(); } }); o.observe(document, {childList: true}); }"
        )
        cdp = page.context.new_cdp_session(page)
        cdp.send("Page.enable")
        cdp.send("Page.addScriptToEvaluateOnNewDocument", {"source": POLL_INSTALL})
        cdp.send("Page.addScriptToEvaluateOnNewDocument", {"source": inject})

        t0 = time.time()

        def on_frame(params):
            frames.append((int((time.time() - t0) * 1000), base64.b64decode(params["data"])))
            try:
                cdp.send("Page.screencastFrameAck", {"sessionId": params["sessionId"]})
            except Exception:
                pass

        cdp.on("Page.screencastFrame", on_frame)
        cdp.send("Page.startScreencast", {"format": "png", "everyNthFrame": 1, "maxWidth": 640, "maxHeight": 900})

        # human flow: search from the homepage box (deep links trip the wall)
        page.fill('input.nav-search-input, input[name="as_word"]', SEARCH_QUERY)
        page.wait_for_timeout(600)
        page.keyboard.press("Enter")
        page.wait_for_load_state("domcontentloaded", timeout=45000)
        page.wait_for_timeout(10000)  # cover sidebar render + in-place swap; pumps CDP events
        try:
            cdp.send("Page.stopScreencast")
        except Exception:
            pass

        samples = page.evaluate("window.__blinkSamples || []")
        final = page.evaluate(
            """() => ({
              url: location.href,
              cards: document.querySelectorAll('ol[class*="ui-search-layout"] > li').length,
              intlBadges: document.querySelectorAll(
                'ol[class*="ui-search-layout"] .poly-component__cbt').length,
              qty: (document.querySelector('[class*="quantity-results"]')||{}).textContent || null,
              styleInstalled: !!document.querySelector('style[data-meli-ld]'),
              swapState: window.__meliLdState || null,
            })"""
        )
        for i, (ts, data) in enumerate(frames):
            (SHOTS / f"f{i:03d}_{ts:05d}ms.png").write_bytes(data)
        print(json.dumps({"frames": len(frames), "samples": samples, "final": final}, indent=2, ensure_ascii=False))
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "recon"
    if mode == "recon":
        recon()
    elif mode == "blink":
        blink()
    else:
        sys.exit(f"unknown mode {mode}")
