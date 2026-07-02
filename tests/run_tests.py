#!/usr/bin/env python3
"""Fixture tests for content.js — run: python3 tests/run_tests.py

Loads each fixture (file://) in a fresh headless Chromium context. Fixtures
define same-world seams (__meliLdGo, __meliLdFetch, mocked chrome.storage)
before loading the real content.js, so no network and no real MeLi.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
FAILED = []


def check(name: str, cond: bool, detail: str = "") -> None:
    tag = "PASS" if cond else "FAIL"
    print(f"  {tag}  {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


def run(browser, fixture: str, waits_ms: int = 1200):
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(f"file://{HERE / fixture}")
    page.wait_for_timeout(waits_ms)
    return ctx, page


def snapshot(page):
    return page.evaluate(
        """() => ({
          state: window.__meliLdState || null,
          nav: window.__navTarget,
          fetches: window.__fetchCalls || [],
          intlHidden: (() => {
            const li = document.getElementById('card-intl-1');
            return li ? getComputedStyle(li).display === 'none' : null;
          })(),
          gridId: (document.querySelector('ol[class*="ui-search-layout"]') || {}).id || '',
          qty: (document.querySelector('[class*="quantity-results"]') || {}).textContent || null,
          pagId: (document.querySelector('ul.andes-pagination') || {}).id || '',
        })"""
    )


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        print("fixture-unfiltered.html — hides intl card, swaps in filtered listing")
        ctx, page = run(browser, "fixture-unfiltered.html")
        s = snapshot(page)
        check("intl card hidden pre-swap", page.evaluate("window.__intlHiddenAtLoad") is True, str(s))
        check("swap happened", s["state"] and s["state"]["swapped"] is True, str(s["state"]))
        check("grid replaced by filtered one", s["gridId"] == "swapped-grid", s["gridId"])
        check("result count updated", s["qty"] == "17.155 resultados", str(s["qty"]))
        check("pagination replaced", s["pagId"] == "pag-filtered", s["pagId"])
        check("fetched MeLi's own Local URL", len(s["fetches"]) == 1 and "10215068" in s["fetches"][0], str(s["fetches"]))
        check("no navigation", s["nav"] is None, str(s["nav"]))
        check("local cards never hidden", page.evaluate(
            "getComputedStyle(document.querySelectorAll('ol li')[0]).display") != "none")
        ctx.close()

        print("fixture-off.html — toggle OFF: no hiding, no fetch, no swap")
        ctx, page = run(browser, "fixture-off.html")
        s = snapshot(page)
        check("OFF reason recorded", s["state"] and s["state"]["reason"] == "OFF", str(s["state"]))
        check("intl card visible", s["intlHidden"] is False, str(s["intlHidden"]))
        check("no fetch", s["fetches"] == [], str(s["fetches"]))
        check("no navigation", s["nav"] is None, str(s["nav"]))
        ctx.close()

        print("fixture-applied.html — filter already applied (removable chip)")
        ctx, page = run(browser, "fixture-applied.html")
        s = snapshot(page)
        check("detected as filtered", s["state"] and s["state"]["reason"] == "already filtered", str(s["state"]))
        check("no fetch", s["fetches"] == [], str(s["fetches"]))
        check("no navigation", s["nav"] is None, str(s["nav"]))
        ctx.close()

        print("fixture-applied-via-hash.html — filter confirmed only by URL hash")
        ctx, page = run(browser, "fixture-applied-via-hash.html")
        s = snapshot(page)
        check("detected as filtered", s["state"] and s["state"]["reason"] == "already filtered", str(s["state"]))
        check("no fetch", s["fetches"] == [], str(s["fetches"]))
        check("no navigation", s["nav"] is None, str(s["nav"]))
        ctx.close()

        print("fixture-flapping.html — MeLi strips hash later; selected link must not re-fire")
        ctx, page = run(browser, "fixture-flapping.html", waits_ms=3000)
        s = snapshot(page)
        check("no swap", not (s["state"] and s["state"]["swapped"]), str(s["state"]))
        check("no fetch", s["fetches"] == [], str(s["fetches"]))
        check("no navigation", s["nav"] is None, str(s["nav"]))
        ctx.close()

        browser.close()

    print()
    if FAILED:
        print(f"{len(FAILED)} FAILED: {FAILED}")
        return 1
    print("ALL GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
