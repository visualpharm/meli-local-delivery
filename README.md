# MeLi Local Delivery — filtra la compra internacional en Mercado Libre

**Extensión de Chrome que oculta los productos importados / de compra internacional en Mercado Libre Argentina.** Fuerza automáticamente el filtro nativo **“Origen del envío: Local”** en cada búsqueda, así ves solo lo que se envía **desde Argentina**: sin demoras de aduana, sin Clave Fiscal, sin esperar 20 días.

Activada por defecto. Un clic la apaga cuando querés ver también lo internacional.

<p align="center">
  <img src="icons/icon128.png" width="96" alt="MeLi Local Delivery — camión con la bandera argentina">
</p>

---

## Qué hace

- **Solo productos nacionales.** Cada búsqueda en `mercadolibre.com.ar` aplica el filtro *Origen del envío → Local* automáticamente.
- **Quita la compra internacional / los productos de China** sin que tengas que tildar el filtro a mano cada vez.
- **Sin parpadeo.** Los importados se ocultan antes del primer render y el filtro se aplica sin recargar la página: el listado nunca se pone en blanco ni «salta».
- **Interruptor de un clic** en la barra de Chrome: ON por defecto, OFF cuando querés ver todo.
- **Cero datos.** No recopila nada, no hace pedidos de red propios, no toca tu cuenta ni el checkout. Solo guarda un booleano (encendido/apagado).

## Por qué es mejor que “borrar” resultados

Otras extensiones **borran del DOM** las publicaciones internacionales y nada más. Eso rompe la paginación, los contadores de resultados y el orden (“24 resultados” que en realidad son 11).

MeLi Local Delivery hace las dos cosas, en orden: primero oculta los importados **antes de que lleguen a dibujarse** (cero parpadeo), y enseguida aplica el **filtro propio de Mercado Libre** — pide la URL del enlace “Local” que el sitio ya genera y reemplaza el listado, el contador y la paginación **sin recargar la página**. Los contadores, el orden y las páginas quedan correctos — porque es el mismo filtro que usarías a mano, aplicado solo.

## Instalar

### Desde la Chrome Web Store
*(próximamente — en revisión)*

### Manual (modo desarrollador)
1. Descargá o cloná este repo.
2. Abrí `chrome://extensions`.
3. Activá **Modo de desarrollador** (arriba a la derecha).
4. **Cargar descomprimida** → elegí esta carpeta.
5. Fijá el ícono del camión 🇦🇷 en la barra.

## Cómo funciona (técnico)

En cualquier página de búsqueda de `mercadolibre.com.ar`, el content script (que corre en `document_start`):

1. **Oculta los importados antes del primer paint**: una regla CSS `:has()` sobre la insignia cross-border de MeLi (`.poly-component__cbt`) más un `MutationObserver` de respaldo que marca las tarjetas cuyo texto accesible empieza con “Internacional”. Nada de esconder la página entera — eso era el parpadeo blanco de la v1.0.
2. **Aplica el filtro real sin navegar**: localiza el enlace de filtro **“Local”** (grupo *Origen del envío*) que arma el propio sitio, hace `fetch` de esa URL (misma origin, con cookies) y reemplaza en el DOM el listado, el contador y la paginación, con `history.replaceState` a la URL filtrada. Si el swap no es posible (markup cambiado, fetch fallido), cae a un `location.replace()` suave.

Nunca hardcodea la codificación de filtros de MeLi (que cambia), así que es estable. Si el filtro ya está aplicado, o el interruptor está en OFF, no hace nada. Guardas anti-bucle por URL evitan acciones repetidas.

## Tests

`tests/` tiene fixtures HTML armadas con el markup real de MeLi (sidebar + tarjetas poly-card) que cargan el `content.js` real con seams (`window.__meliLdGo`, `window.__meliLdFetch`) y un `chrome.storage` simulado. Correr: `python3 tests/run_tests.py` (Playwright headless, sin red). Cubre: oculta el importado antes del swap, swap del listado/contador/paginación, no re-fetchea si ya está filtrado, no hace bucle cuando MeLi borra el hash, respeta el OFF.

---

## Palabras clave

extensión chrome mercado libre · filtrar compra internacional mercado libre · ocultar productos del exterior mercado libre · sacar productos de china mercado libre · comprar solo productos nacionales argentina · envío desde argentina filtro · origen del envío local · mercadolibre international shipping filter · hide imported products mercadolibre.

## Autor

Hecho por **[Ivan Braun](https://aiandtractors.com)** — emprendedor y fundador de [Icons8](https://icons8.com) y [Generated Photos](https://generated.photos). Más en **[aiandtractors.com](https://aiandtractors.com)**.

## Licencia

MIT.
