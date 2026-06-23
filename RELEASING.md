# Releasing

> **The text you paste into the console lives in [`store/STORE-LISTING.md`](store/STORE-LISTING.md)** — name, summary, description, permission justifications, privacy. Open that file and copy from it.

## v1 — one time, in the console (mints the extension ID)

The Chrome Web Store API can upload the *package* but **cannot** create the
store listing (description, screenshots, category, privacy). So the first
publish happens in the console:

1. https://chrome.google.com/webstore/devconsole → **New item**.
2. Upload `dist/meli-local-delivery-v1.0.0.zip`.
3. Paste copy from `store/STORE-LISTING.md`; add `store/promo-1280x800.png`
   (1280×800) and the 128px icon; set **Developer website** = `aiandtractors.com`.
4. Visibility **Public** → Submit.
5. Copy the **Item ID** from the console URL — that's your `CWS_EXTENSION_ID`.

## Automated releases — every version after v1

### One-time API setup
1. **Google Cloud Console** → same project as the dev account →
   *APIs & Services* → enable **Chrome Web Store API**.
2. *Credentials* → **Create credentials → OAuth client ID → Desktop app**.
   Save the **Client ID** and **Client secret**.
3. Get a refresh token:
   ```bash
   python3 scripts/get_cws_refresh_token.py <CLIENT_ID> <CLIENT_SECRET>
   ```
   Authorize in the browser; it prints the **refresh token**.
4. Add four **GitHub repo secrets** (Settings → Secrets → Actions):
   `CWS_EXTENSION_ID`, `CWS_CLIENT_ID`, `CWS_CLIENT_SECRET`, `CWS_REFRESH_TOKEN`.

### Ship a new version
Bump `"version"` in `manifest.json`, then:
```bash
git tag v1.0.1 && git push --tags
```
GitHub Actions builds the zip and publishes it. No console.

### Or locally
```bash
cp .env.cws.example .env.cws   # fill in the 4 values
set -a; source .env.cws; set +a
./scripts/release.sh
```
