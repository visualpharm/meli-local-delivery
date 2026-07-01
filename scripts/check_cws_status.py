#!/usr/bin/env python3
"""
check_cws_status.py — daily Chrome Web Store review-status check for the
"MeLi Local Delivery" extension. Detects when the listing goes live (or when an
upload/validation error appears) and pings Ivan on any *change* of status.

Two best-effort signals, in order of authority:

  1. CWS API (used only if the 4 OAuth creds are present):
     items.get?projection=DRAFT -> uploadState (SUCCESS/IN_PROGRESS/FAILURE/
     NOT_FOUND) + itemError[]. This catches package upload/validation failures.
     NOTE: the public CWS API does NOT expose the human review verdict
     (in-review vs published vs rejected) — Google never exposed it — so the API
     alone can't tell you "it's live". That's what signal 2 is for.

  2. Public listing probe: GET https://chromewebstore.google.com/detail/<ID>
     -> reachable listing page = PUBLISHED (live); not-found = NOT_PUBLIC
     (still in review, rejected, or the item was never created).

Config (env vars, or a `.env.cws` file next to the repo root — gitignored):
  CWS_EXTENSION_ID                                   (required to check anything)
  CWS_CLIENT_ID / CWS_CLIENT_SECRET / CWS_REFRESH_TOKEN   (optional -> enables API)

State is persisted to scripts/.cws-status-state.json (gitignored). When the
derived status differs from the last run, Ivan gets a Telegram ping (bot token
from ~/.claude/channels/telegram/.env; chat = Ivan, 288205285 — self-notify,
exempt from the outbox guard).

Exit code is always 0 unless something truly unexpected happens — this is a cron
job, not a test. Designed for a daily LaunchAgent; harmless to run by hand.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATE_FILE = REPO / "scripts" / ".cws-status-state.json"
ENV_FILE = REPO / ".env.cws"
IVAN_TG_CHAT = "288205285"
TG_ENV = Path.home() / ".claude" / "channels" / "telegram" / ".env"


def log(msg):
    print(f"[cws-check {time.strftime('%Y-%m-%dT%H:%M:%S%z')}] {msg}", flush=True)


def load_env():
    """Merge process env with .env.cws (process env wins)."""
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("CWS_EXTENSION_ID", "CWS_CLIENT_ID", "CWS_CLIENT_SECRET",
              "CWS_REFRESH_TOKEN"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def read_secret(path, key):
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return None


# ---------------------------------------------------------------------------
# Signal 1 — CWS API (authoritative for upload errors)
# ---------------------------------------------------------------------------
def get_access_token(env):
    data = urllib.parse.urlencode({
        "client_id": env["CWS_CLIENT_ID"],
        "client_secret": env["CWS_CLIENT_SECRET"],
        "refresh_token": env["CWS_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["access_token"]


def api_item_status(env):
    """Returns dict with uploadState/itemError/crxVersion, or None if no creds."""
    if not all(env.get(k) for k in ("CWS_CLIENT_ID", "CWS_CLIENT_SECRET",
                                    "CWS_REFRESH_TOKEN")):
        return None
    token = get_access_token(env)
    url = (f"https://www.googleapis.com/chromewebstore/v1.1/items/"
           f"{env['CWS_EXTENSION_ID']}?projection=DRAFT")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "x-goog-api-version": "2",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


# ---------------------------------------------------------------------------
# Signal 2 — public listing probe (authoritative for "is it live")
# ---------------------------------------------------------------------------
def is_live(ext_id):
    """True if the public store detail page is a real published listing.

    chromewebstore.google.com is a JS SPA, so the install UI is never in the
    server HTML — grepping the body is useless. The reliable tell is the
    redirect: a PUBLISHED item is 301'd to /detail/<real-name-slug>/<id>,
    while an item that isn't public (never created, in review, rejected) lands
    on the placeholder /detail/empty-title/<id>. So we key off the slug.
    """
    url = f"https://chromewebstore.google.com/detail/{ext_id}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0 Safari/537.36",
        "Accept-Language": "es-AR,es;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            final = r.geturl()
            r.read(1)  # drain a byte; we only care about the redirect target
        parts = urllib.parse.urlparse(final).path.strip("/").split("/")
        # Expected shape: ["detail", "<slug>", "<id>"].
        slug = parts[1] if len(parts) >= 3 and parts[0] == "detail" else ""
        if slug and slug not in ("empty-title", ext_id):
            return True, f"live: /detail/{slug}/{ext_id}"
        return False, f"not-public: {final}"
    except urllib.error.HTTPError as e:
        return False, f"http {e.code}"
    except Exception as e:  # noqa: BLE001 — best-effort probe
        return None, f"probe-error: {e}"


def notify(text):
    token = read_secret(TG_ENV, "TELEGRAM_BOT_TOKEN")
    if not token:
        log("no telegram token — skipping notify; message was:\n" + text)
        return
    data = urllib.parse.urlencode({
        "chat_id": IVAN_TG_CHAT,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode()
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage", data=data)
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read()
        log("notified Ivan via Telegram")
    except Exception as e:  # noqa: BLE001
        log(f"telegram notify failed: {e}")


def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def main():
    env = load_env()
    ext_id = env.get("CWS_EXTENSION_ID")
    if not ext_id:
        log("CWS_EXTENSION_ID not set — nothing to check yet. Create the item in "
            "the dev console, then put the ID in .env.cws. Exiting quietly.")
        return 0

    detail = {"ext_id": ext_id}

    # Signal 1: API upload state (if creds present).
    api_status = None
    try:
        api = api_item_status(env)
        if api is not None:
            api_status = api.get("uploadState")
            detail["uploadState"] = api_status
            detail["itemError"] = api.get("itemError")
            detail["crxVersion"] = api.get("crxVersion")
    except Exception as e:  # noqa: BLE001
        detail["api_error"] = str(e)
        log(f"API check failed (continuing with public probe): {e}")

    # Signal 2: public probe (is it live?).
    live, why = is_live(ext_id)
    detail["live_probe"] = why

    # Derive a single status label.
    if detail.get("itemError"):
        status = "UPLOAD_ERROR"
    elif live is True:
        status = "PUBLISHED"
    elif live is False:
        status = "IN_REVIEW_OR_REJECTED"
    else:
        status = "UNKNOWN"
    detail["status"] = status

    prev = load_state()
    prev_status = prev.get("status")
    log(f"status={status} (was {prev_status}) detail={json.dumps(detail)}")

    if status != prev_status:
        store_url = f"https://chromewebstore.google.com/detail/{ext_id}"
        if status == "PUBLISHED":
            msg = (
                "✅ MeLi Local Delivery está APROBADA y en vivo en la Chrome Web "
                f"Store:\n{store_url}\n\n"
                "Cerrar el loop:\n"
                "• aiandtractors/pages/meli.js → poné STORE_URL = la URL de arriba\n"
                "• Reddit console: pasá los 3 posts consumer (r/argentina, "
                "r/RepublicaArgentina, r/AskArgentina) de 'draft' a 'ready'")
        elif status == "UPLOAD_ERROR":
            errs = detail.get("itemError") or []
            msg = ("⚠️ MeLi Local Delivery: la Web Store reportó errores de "
                   f"subida:\n{json.dumps(errs, ensure_ascii=False, indent=2)}")
        elif status == "IN_REVIEW_OR_REJECTED":
            msg = ("⏳ MeLi Local Delivery: el item existe pero todavía NO está "
                   f"público (en revisión o rechazado). Probe: {why}")
        else:
            msg = f"MeLi Local Delivery status → {status}. Detail: {why}"
        notify(msg)

    save_state({"status": status, "detail": detail,
                "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
