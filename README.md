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
- **Interruptor de un clic** en la barra de Chrome: ON por defecto, OFF cuando querés ver todo.
- **Cero datos.** No recopila nada, no hace pedidos de red propios, no toca tu cuenta ni el checkout. Solo guarda un booleano (encendido/apagado).

## Por qué es mejor que “borrar” resultados

Otras extensiones **borran del DOM** las publicaciones internacionales. Eso rompe la paginación, los contadores de resultados y el orden (“24 resultados” que en realidad son 11).

MeLi Local Delivery usa el **filtro propio de Mercado Libre**: sigue el enlace “Local” que el sitio ya genera y redirige a los resultados filtrados de verdad. Los contadores, el orden y las páginas quedan correctos — porque es el mismo filtro que usarías a mano, aplicado solo.

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

En cualquier página de búsqueda de `mercadolibre.com.ar`, el content script localiza el enlace de filtro **“Local”** (grupo *Origen del envío*) que arma el propio sitio y sigue esa URL. Nunca hardcodea la codificación de filtros de MeLi (que cambia), así que es estable. Si el filtro ya está aplicado, o el interruptor está en OFF, no hace nada. Guardas anti-bucle por URL evitan redirecciones repetidas.

## Tests

`tests/` tiene fixtures HTML armadas con el markup real del sidebar de MeLi que cargan el `content.js` real con un seam de navegación (`window.__meliLdGo`) y un `chrome.storage` simulado. Verificadas con Playwright (filtro aplica / no hace bucle / respeta el OFF).

---

## Palabras clave

extensión chrome mercado libre · filtrar compra internacional mercado libre · ocultar productos del exterior mercado libre · sacar productos de china mercado libre · comprar solo productos nacionales argentina · envío desde argentina filtro · origen del envío local · mercadolibre international shipping filter · hide imported products mercadolibre.

## Autor

Hecho por **[Ivan Braun](https://aiandtractors.com)** — emprendedor y fundador de [Icons8](https://icons8.com) y [Generated Photos](https://generated.photos). Más en **[aiandtractors.com](https://aiandtractors.com)**.

## Licencia

MIT.
