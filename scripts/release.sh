#!/usr/bin/env bash
# Publish a new version to the Chrome Web Store via the API (no console needed).
# Works for UPDATES to an already-listed item (v1 must be created in the console once).
#
# Requires these env vars (put them in .env.cws — gitignored — and `source` it):
#   CWS_CLIENT_ID, CWS_CLIENT_SECRET, CWS_REFRESH_TOKEN, CWS_EXTENSION_ID
#
# Usage: ./scripts/release.sh [path/to.zip]   (defaults to the built dist zip)
set -euo pipefail
cd "$(dirname "$0")/.."

ZIP="${1:-dist/meli-local-delivery-v$(python3 -c 'import json;print(json.load(open("manifest.json"))["version"])').zip}"
[ -f "$ZIP" ] || { echo "zip not found: $ZIP — build it first"; exit 1; }

for v in CWS_CLIENT_ID CWS_CLIENT_SECRET CWS_REFRESH_TOKEN CWS_EXTENSION_ID; do
  [ -n "${!v:-}" ] || { echo "missing env: $v (source .env.cws)"; exit 1; }
done

echo "→ getting access token"
ACCESS_TOKEN=$(curl -fsS -X POST https://oauth2.googleapis.com/token \
  -d client_id="$CWS_CLIENT_ID" \
  -d client_secret="$CWS_CLIENT_SECRET" \
  -d refresh_token="$CWS_REFRESH_TOKEN" \
  -d grant_type=refresh_token \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

echo "→ uploading $ZIP to item $CWS_EXTENSION_ID"
curl -fsS -X PUT \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "x-goog-api-version: 2" \
  -T "$ZIP" \
  "https://www.googleapis.com/upload/chromewebstore/v1.1/items/$CWS_EXTENSION_ID" \
  | python3 -m json.tool

echo "→ publishing"
curl -fsS -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "x-goog-api-version: 2" \
  -H "Content-Length: 0" \
  "https://www.googleapis.com/chromewebstore/v1.1/items/$CWS_EXTENSION_ID/publish" \
  | python3 -m json.tool

echo "✓ submitted for review"
