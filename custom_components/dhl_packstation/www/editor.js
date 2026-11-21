import { escapeHTML as esc, stations, text } from "./data.js";

class PackstationCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.shadowRoot.addEventListener("change", (event) => this._change(event));
    this.shadowRoot.addEventListener("click", (event) => this._move(event));
  }

  setConfig(config) { this._config = { ...config }; this._render(); }
  set hass(hass) { this._hass = hass; this._render(); }

  _change(event) {
    const input = event.target;
    const config = { ...this._config };
    if (input.name === "title") config.title = input.value;
    if (input.name === "station") config.station = input.value;
    if (input.name === "show_exact") config.show_exact = input.checked;
    if (input.name === "stations") {
      const selected = new Set(config.stations);
      if (input.checked) selected.add(input.value);
      else selected.delete(input.value);
      config.stations = [...selected];
    }
    this._save(config);
  }

  _move(event) {
    const button = event.target.closest("button[data-step]");
    if (!button || button.getAttribute("aria-disabled") === "true") return;
    const selected = [...new Set(this._config.stations)];
    const from = selected.indexOf(button.dataset.station), to = from + Number(button.dataset.step);
    if (from < 0 || to < 0 || to >= selected.length) return;
    [selected[from], selected[to]] = [selected[to], selected[from]];
    this._save({ ...this._config, stations: selected });
  }

  _save(config) {
    const reordered = config.stations !== this._config.stations;
    this._config = config;
    if (reordered) this._render();
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
  }

  _render() {
    if (!this._config || !this._hass) return;
    const labels = text(this._hass), items = stations(this._hass);
    const overview = this._config.type === "custom:dhl-packstation-overview-card";
    const selected = new Set(overview ? this._config.stations : []);
    const byId = new Map(items.map((item) => [item.id, item]));
    const choices = overview
      ? [...Array.from(selected, (id) => byId.get(id) ?? { id }), ...items.filter((item) => !selected.has(item.id))]
      : items;
    const options = choices.map((item, index) => {
      const name = item.meta
        ? `${labels.station} ${item.meta.station_number} · ${item.meta.postal_code} ${item.meta.city || ""}`
        : `${labels.stationUnavailable} · ${item.id}`;
      return overview
        ? `<div class="station-option"><label class="check"><input type="checkbox" name="stations" value="${esc(item.id)}" ${selected.has(item.id) ? "checked" : ""}>${esc(name)}</label>${selected.has(item.id) && selected.size > 1 ? `
          <button type="button" data-station="${esc(item.id)}" data-step="-1" aria-label="${esc(`${labels.moveUp}: ${name}`)}" aria-disabled="${index === 0}">↑</button>
          <button type="button" data-station="${esc(item.id)}" data-step="1" aria-label="${esc(`${labels.moveDown}: ${name}`)}" aria-disabled="${index === selected.size - 1}">↓</button>` : ""}</div>`
        : `<option value="${esc(item.id)}" ${this._config.station === item.id ? "selected" : ""}>${esc(name)}</option>`;
    }).join("");
    const html = `<style>
      :host { display:block; color:var(--primary-text-color); font-family:inherit; }
      label,legend { font-size:14px; line-height:1.5; } .field { display:grid; gap:8px; margin:16px 0; }
      input[type="text"],select { box-sizing:border-box; width:100%; min-height:44px; border:1px solid var(--divider-color,#888); border-radius:6px; padding:10px; color:var(--primary-text-color); background:var(--card-background-color); font:inherit; }
      fieldset { min-width:0; border:1px solid var(--divider-color,#888); border-radius:6px; margin:16px 0; }
      .check { display:flex; align-items:center; gap:10px; min-height:44px; overflow-wrap:anywhere; } input[type="checkbox"] { flex:none; width:20px; height:20px; }
      .station-option { display:grid; grid-template-columns:minmax(0,1fr) repeat(2,auto); align-items:center; gap:4px; }
      .station-option button { min-width:44px; min-height:44px; padding:0; border:1px solid var(--divider-color,#888); border-radius:6px; background:var(--card-background-color); color:inherit; font-size:18px; cursor:pointer; }
      .station-option button[aria-disabled="true"] { opacity:.45; cursor:default; }
      p { color:var(--secondary-text-color); font-size:13px; } :focus-visible { outline:2px solid var(--primary-color,#03a9f4); outline-offset:2px; }
    </style>
    <label class="field">${esc(labels.title)}<input type="text" name="title" value="${esc(this._config.title ?? "")}" placeholder="${esc(overview ? labels.overview : labels.free)}"></label>
    ${overview ? `<fieldset><legend>${esc(labels.selection)}</legend><p>${esc(labels.all)} ${esc(labels.orderHint)}</p>${options}</fieldset>` : `<label class="field">${esc(labels.station)}<select name="station">${options || `<option value="">${esc(labels.empty)}</option>`}</select></label>`}
    <label class="check"><input type="checkbox" name="show_exact" ${this._config.show_exact ? "checked" : ""}>${esc(labels.exact)}</label>`;
    if (html === this._html) return;
    const focused = this.shadowRoot.activeElement;
    this._html = html;
    this.shadowRoot.innerHTML = html;
    if (focused?.matches("button[data-step]")) {
      const replacement = [...this.shadowRoot.querySelectorAll("button[data-step]")].find(
        (button) => button.dataset.station === focused.dataset.station && button.dataset.step === focused.dataset.step);
      replacement?.focus({ preventScroll: true });
    } else if (focused?.name === "stations") {
      const inputs = [...this.shadowRoot.querySelectorAll('input[name="stations"]')];
      const replacement = inputs.find((input) => input.value === focused.value) ?? inputs[0];
      replacement?.focus({ preventScroll: true });
    }
  }
}

if (!customElements.get("dhl-packstation-card-editor")) customElements.define("dhl-packstation-card-editor", PackstationCardEditor);
