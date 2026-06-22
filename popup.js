const KEY = "localDeliveryEnabled";
const sw = document.getElementById("sw");
const stateEl = document.getElementById("state");

function render(on) {
  sw.checked = on;
  document.body.classList.toggle("on", on);
  stateEl.textContent = on
    ? "ON — fuerzo “Origen del envío: Local” en cada búsqueda."
    : "OFF — muestro todos los resultados, sin filtrar.";
}

chrome.storage.sync.get({ [KEY]: true }, (c) => render(c[KEY] !== false));

sw.addEventListener("change", () => {
  const on = sw.checked;
  chrome.storage.sync.set({ [KEY]: on }, () => {
    render(on);
    // Reload the active MeLi tab so the change takes effect immediately.
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const t = tabs[0];
      if (t && /mercadolibre\.com\.ar/.test(t.url || "")) chrome.tabs.reload(t.id);
    });
  });
});
