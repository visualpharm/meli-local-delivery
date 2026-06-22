# Chrome Web Store listing — MeLi Local Delivery

## Store name
MeLi Local Delivery

## Summary (≤132 chars)
Fuerza el filtro “Origen del envío: Local” en MercadoLibre Argentina. Solo productos que se envían desde el país.

## Category
Shopping

## Language
Spanish (Argentina) — es-419

## Description
MeLi Local Delivery aplica automáticamente el filtro **“Origen del envío: Local”**
en cada búsqueda de MercadoLibre Argentina, para que veas solo los productos que
se envían **desde dentro del país** — sin demoras de aduana ni envíos
internacionales.

• Activado por defecto: cada búsqueda se filtra sola.
• Un clic en el ícono lo apaga cuando querés ver todo (incluido lo internacional).
• No toca tu cuenta ni el checkout: solo aplica el filtro de búsqueda que ya
  existe en MercadoLibre.

Funciona siguiendo el propio enlace de filtro “Local” que arma MercadoLibre, así
que se mantiene estable aunque cambien las URLs internas del sitio.

## Single purpose (required by Google)
Apply MercadoLibre Argentina's existing "Origen del envío: Local" search filter
automatically, with a one-click on/off toggle.

## Permission justifications (required by Google)
- **storage** — Save the single on/off preference for the filter. Nothing else
  is stored.
- **host permission `*://*.mercadolibre.com.ar/*`** — The extension only runs on
  MercadoLibre Argentina pages, where it reads the search sidebar to find the
  "Local" filter link and redirects the current tab to the filtered results.

## Privacy
- Does **not** collect, transmit, or sell any user data.
- No analytics, no remote servers, no network requests of its own.
- The only stored value is a boolean (filter on/off) in `chrome.storage.sync`.

## Assets
- Icon: `icons/icon128.png`
- Screenshot / promo: `store/promo-1280x800.png`

## Publish steps (require Ivan — Google account + one-time fee)
1. https://chrome.google.com/webstore/devconsole — sign in with the Google
   account that will own the listing.
2. Pay the one-time **US$5** developer registration fee (first time only).
3. **New item** → upload `dist/meli-local-delivery-v1.0.0.zip`.
4. Fill name/summary/description/category from this file; upload the 1280×800
   screenshot and the 128px icon.
5. Set **Visibility** (Unlisted = link-only, or Public). Submit for review
   (~1–3 days).
