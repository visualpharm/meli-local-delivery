# Chrome Web Store listing — MeLi Local Delivery

## Store name
MeLi Local Delivery — filtra la compra internacional

## Summary (≤132 chars)
Oculta los productos importados en Mercado Libre. Fuerza el filtro “Origen del envío: Local”. Solo envíos desde Argentina.

## Category
Shopping

## Language
Spanish (Argentina) — es-419

## Visibility
**Public** (so anyone can find and install it from search).

## Developer website
https://aiandtractors.com

## Description (SEO-optimized — keywords woven in naturally)
¿Cansado de que Mercado Libre te llene la búsqueda de productos de **compra
internacional** que tardan 20 días y necesitan Clave Fiscal? **MeLi Local
Delivery** los oculta automáticamente.

La extensión fuerza el filtro **nativo** de Mercado Libre **“Origen del envío:
Local”** en cada búsqueda, así ves **solo productos que se envían desde
Argentina** — sin aduana, sin demoras, sin importados de China.

✅ Filtra la compra internacional automáticamente, en cada búsqueda
✅ Solo productos nacionales, con envío local
✅ Interruptor de un clic: encendido por defecto, apagalo cuando quieras ver todo
✅ Liviana y privada: no recopila datos, no toca tu cuenta ni el pago

**¿Por qué es mejor que las que “borran” resultados?** Otras extensiones eliminan
las publicaciones del DOM y rompen la paginación y los contadores. Esta usa el
**propio filtro de Mercado Libre**, así que el orden, las páginas y la cantidad
de resultados quedan correctos.

Ideal para quien compra en Mercado Libre Argentina y quiere **evitar los
productos del exterior** y recibir rápido, con envío nacional.

Palabras clave: filtrar compra internacional mercado libre, ocultar productos
del exterior, sacar productos de china, comprar solo nacional, envío desde
Argentina, origen del envío local, extensión chrome mercado libre.

## Single purpose (required by Google)
Apply MercadoLibre Argentina's native "Origen del envío: Local" search filter
automatically, hiding international-purchase listings, with a one-click on/off toggle.

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
- Screenshot / promo (1280×800): `store/promo-1280x800.png`

## Publish steps (require Ivan — Google account + one-time fee)
1. https://chrome.google.com/webstore/devconsole — sign in.
2. Pay the one-time **US$5** developer registration fee (first time only).
3. **New item** → upload `dist/meli-local-delivery-v1.0.0.zip`.
4. Paste name/summary/description/category from this file; upload the 1280×800
   screenshot and the 128px icon; set **Developer website** = aiandtractors.com.
5. **Visibility = Public** → submit for review (~1–3 days).
