import { escapeHTML as esc, stations, text } from "./data.js";

class PackstationCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.shadowRoot.addEventListener("change", (event) => this._change(event));
  }

  setConfig(config) { this._config = { ...config }; this._render(); }
  set hass(hass) { this._hass = hass; this._render(); }

  _change(event) {
    const input = event.target;
    const config = { ...this._config };
    if (input.name === "title") config.title = input.value;
    if (input.name === "station") config.station = input.value;
    if (input.name === "show_exact") config.show_exact = input.checked;
    if (input.name === "stations") config.stations = [...this.shadowRoot.querySelectorAll('input[name="stations"]:checked')].map((item) => item.value);
    this._config = config;
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
  }

  _render() {
    if (!this._config || !this._hass) return;
    const labels = text(this._hass), items = stations(this._hass);
    const overview = this._config.type === "custom:dhl-packstation-overview-card";
    const selected = this._config.stations || [];
    const options = items.map((item) => {
      const name = `${labels.station} ${item.meta.station_number} · ${item.meta.postal_code} ${item.meta.city || ""}`;
      return overview
        ? `<label class="check"><input type="checkbox" name="stations" value="${esc(item.id)}" ${selected.includes(item.id) ? "checked" : ""}>${esc(name)}</label>`
        : `<option value="${esc(item.id)}" ${this._config.station === item.id ? "selected" : ""}>${esc(name)}</option>`;
    }).join("");
    const html = `<style>
      :host { display:block; color:var(--primary-text-color); font-family:inherit; }
      label,legend { font-size:14px; line-height:1.5; } .field { display:grid; gap:8px; margin:16px 0; }
      input[type="text"],select { box-sizing:border-box; width:100%; min-height:44px; border:1px solid var(--divider-color,#888); border-radius:6px; padding:10px; color:var(--primary-text-color); background:var(--card-background-color); font:inherit; }
      fieldset { border:1px solid var(--divider-color,#888); border-radius:6px; margin:16px 0; }
      .check { display:flex; align-items:center; gap:10px; min-height:44px; } input[type="checkbox"] { width:20px; height:20px; }
      p { color:var(--secondary-text-color); font-size:13px; } :focus-visible { outline:2px solid var(--primary-color,#03a9f4); outline-offset:2px; }
    </style>
    <label class="field">${esc(labels.title)}<input type="text" name="title" value="${esc(this._config.title ?? "")}" placeholder="${esc(overview ? labels.overview : labels.free)}"></label>
    ${overview ? `<fieldset><legend>${esc(labels.selection)}</legend><p>${esc(labels.all)}</p>${options}</fieldset>` : `<label class="field">${esc(labels.station)}<select name="station">${options || `<option value="">${esc(labels.empty)}</option>`}</select></label>`}
    <label class="check"><input type="checkbox" name="show_exact" ${this._config.show_exact ? "checked" : ""}>${esc(labels.exact)}</label>`;
    if (html !== this._html) { this._html = html; this.shadowRoot.innerHTML = html; }
  }
}

if (!customElements.get("dhl-packstation-card-editor")) customElements.define("dhl-packstation-card-editor", PackstationCardEditor);
