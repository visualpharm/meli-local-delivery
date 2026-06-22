#!/usr/bin/env python3
"""One-time: get a Chrome Web Store API refresh token.

Prereq: a Google Cloud "Desktop app" OAuth client (client_id + secret) with the
Chrome Web Store API enabled on the project.

Usage:
    python3 scripts/get_cws_refresh_token.py <CLIENT_ID> <CLIENT_SECRET>

It opens the Google consent screen, captures the code on a local redirect, and
prints the refresh token to paste into .env.cws (and GitHub repo secrets).
"""
import sys, json, urllib.parse, urllib.request, webbrowser, http.server, threading

SCOPE = "https://www.googleapis.com/auth/chromewebstore"
PORT = 8123
REDIRECT = f"http://localhost:{PORT}/"

if len(sys.argv) != 3:
    print(__doc__)
    sys.exit(1)
client_id, client_secret = sys.argv[1], sys.argv[2]

code_holder = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(q)
        code_holder["code"] = params.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("<h2>OK — volvé a la terminal.</h2>".encode())

    def log_message(self, *a):
        pass


auth_url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode({
    "client_id": client_id,
    "redirect_uri": REDIRECT,
    "response_type": "code",
    "scope": SCOPE,
    "access_type": "offline",
    "prompt": "consent",
})

srv = http.server.HTTPServer(("localhost", PORT), Handler)
threading.Thread(target=srv.handle_request, daemon=True).start()
print("Opening consent screen… authorize in the browser.")
webbrowser.open(auth_url)
print(auth_url)

while "code" not in code_holder:
    pass
code = code_holder["code"]
if not code:
    print("No code received.")
    sys.exit(1)

data = urllib.parse.urlencode({
    "code": code,
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": REDIRECT,
    "grant_type": "authorization_code",
}).encode()
resp = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", data))
print("\n=== REFRESH TOKEN ===")
print(resp.get("refresh_token", "(none — revoke prior grant and retry with prompt=consent)"))
print("=====================")
