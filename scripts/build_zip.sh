#!/usr/bin/env bash
# Build the uploadable extension zip into dist/, named by manifest version.
# Same file list the GitHub Action ships. Run before ./scripts/release.sh or a
# manual console upload.
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION=$(python3 -c 'import json;print(json.load(open("manifest.json"))["version"])')
ZIP="dist/meli-local-delivery-v${VERSION}.zip"
mkdir -p dist
rm -f "$ZIP"

zip -j -X "$ZIP" manifest.json content.js popup.html popup.js >/dev/null
zip -X "$ZIP" icons/icon16.png icons/icon48.png icons/icon128.png >/dev/null

echo "✓ built $ZIP"
unzip -l "$ZIP"
