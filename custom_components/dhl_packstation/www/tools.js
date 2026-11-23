import { SIZES, escapeHTML as esc, language } from "./data.js";
import { COPY, coordinates, directions, fitLabel, packageFit } from "./station-view.js";

class PackstationTools extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.shadowRoot.addEventListener("submit", (event) => this._submit(event));
    this.shadowRoot.addEventListener("input", (event) => {
      if (SIZES.includes(event.target.name)) {
        this._updateFit();
        this.dispatchEvent(new Event("packstation-demand"));
      }
    });
    this.shadowRoot.addEventListener("change", (event) => {
      if (event.target.name === "station") {
        this._selected = new Set(new FormData(event.target.form).getAll("station"));
      }
    });
  }

  update(hass, stations, all) {
    this._hass = hass;
    this._stations = stations;
    this._all = all;
    if (this._map) this._map.hass = hass;
    this._render();
    this._updateFit();
  }

  get demand() {
    if (this._alarm?.sizes) return this._alarm.sizes;
    const form = this.shadowRoot.querySelector("form");
    if (!form) return {};
    const data = new FormData(form);
    return Object.fromEntries(SIZES.map((size) => [size, Number(data.get(size))]));
  }

  _updateFit() {
    const labels = COPY[language(this._hass)], demand = this.demand;
    this.shadowRoot.querySelectorAll(".station-fit").forEach((element, index) => {
      const fit = packageFit(this._stations[index], demand);
      element.className = `station-fit ${fit?.state ?? ""}`;
      const label = fitLabel(fit, labels);
      if (element.textContent !== label) element.textContent = label;
    });
  }

  async _submit(event) {
    event.preventDefault();
    const data = new FormData(event.target);
    const labels = COPY[language(this._hass)];
    let action = "stop_alarm";
    let payload = {};
    if (this._alarm.status !== "waiting" && this._alarm.status !== "matched") {
      action = "start_alarm";
      payload = this.demand;
      payload.stations = data.getAll("station");
      payload.notifier = data.get("notifier");
      if (!payload.stations.length || !SIZES.some((size) => payload[size])) {
        this.shadowRoot.querySelector("[role=status]").textContent = labels.empty;
        return;
      }
    }
    const button = event.submitter;
    if (button) button.disabled = true;
    try {
      await this._hass.callService("dhl_packstation", action, payload);
      this.shadowRoot.querySelector("[role=status]").textContent = "";
    } catch {
      this.shadowRoot.querySelector("[role=status]").textContent = labels.error;
    } finally {
      if (button) button.disabled = false;
    }
  }

  async _openMap(entities) {
    const container = this.shadowRoot.querySelector(".map-content");
    if (!entities.length || typeof window.loadCardHelpers !== "function" || container === this._mapTarget) return;
    this._mapTarget = container;
    try {
      const helpers = await window.loadCardHelpers();
      if (container !== this.shadowRoot.querySelector(".map-content")) return;
      this._map = helpers.createCardElement({ type: "map", entities, auto_fit: true });
      this._map.hass = this._hass;
      container.append(this._map);
    } catch {
      this._mapTarget = null;
    }
  }

  _render() {
    const labels = COPY[language(this._hass)];
    this._alarm = this._all.find((item) => item.entities.free_total?.attributes.alarm)?.entities.free_total.attributes.alarm ?? {};
    const mapItems = this._stations.filter(coordinates);
    const notifications = Object.keys(this._hass?.services?.notify || {}).filter((key) => key.startsWith("mobile_app_")).sort();
    const stations = this._stations.map((item) => [item.id, item.meta.station_number, item.meta.city || item.meta.postal_code]);
    const locations = mapItems.map(item => [item.id, item.meta.location_name, coordinates(item)]);
    const signature = JSON.stringify([labels.alarm, this._alarm, stations, notifications, locations, this._hass?.user?.is_admin]);
    if (signature === this._signature) return;
    this._signature = signature;
    const wasOpen = this.shadowRoot.querySelector(".alarm")?.open;
    const mapOpen = this.shadowRoot.querySelector(".map")?.open;
    const previous = this.shadowRoot.querySelector("form");
    const draft = previous ? new FormData(previous) : null;
    const enabled = this._hass?.user?.is_admin !== false && this._all.some(item => item.entities.free_total);
    const state = this._alarm.status;
    const match = this._all.find((item) => item.id === this._alarm.match);
    const requested = SIZES.filter(size => this._alarm.sizes?.[size]).map(size => `${this._alarm.sizes[size]}× ${size.toUpperCase()}`).join(" · ");
    this.shadowRoot.innerHTML = `<style>
      :host{display:block;color:var(--primary-text-color);font:inherit}
      details{margin-top:8px;border:1px solid var(--divider-color,#777);border-radius:12px;padding:0 12px}
      summary{padding:10px 0;cursor:pointer;font-weight:600}
      form,.map-content{padding-bottom:12px} fieldset{min-width:0;margin:0 0 10px;border:1px solid var(--divider-color,#777);border-radius:8px}
      label{font-size:14px} .station-choice{display:flex;gap:6px;align-items:center;min-height:32px;overflow-wrap:anywhere}
      .pack-counts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}
      .pack-counts label,.notify{display:grid;gap:4px} input[type=number],select{box-sizing:border-box;width:100%;min-height:36px;background:var(--card-background-color,#eee);color:var(--primary-text-color,#222);border:1px solid var(--divider-color,#777);border-radius:6px;padding:4px}
      button{margin-top:10px;min-height:40px;padding:6px 12px;border:1px solid var(--divider-color,#777);border-radius:8px;background:var(--secondary-background-color,#eee);color:inherit;cursor:pointer;font:inherit}
      a{color:var(--primary-color);display:inline-flex;min-height:28px;align-items:center} p{margin:6px 0}
      .directions{display:flex;flex-wrap:wrap;gap:0 12px}
      .map-station{padding-bottom:6px;font-size:13px} .station-fit{display:block;font-size:12px;color:var(--secondary-text-color,#aaa)} .station-fit.fits{color:var(--success-color,#89bd3d)} .hint{font-size:12px;color:var(--secondary-text-color,#aaa)}
    </style>
    ${enabled && stations.length ? `<details class="alarm" ${wasOpen ? "open" : ""}><summary>${esc(labels.alarm)}${state ? ` · ${esc(labels[state])}` : ""}</summary><form>
      ${state ? `<p>${esc(requested)}${match ? ` · Packstation ${esc(match.meta.station_number)}` : ""}</p>` : `
      <fieldset><legend>${esc(labels.sizes)}</legend><div class="pack-counts">${SIZES.map(size => `<label>${size.toUpperCase()}<input type="number" min="0" max="99" step="1" name="${size}" value="${esc(draft?.get(size) ?? 0)}"></label>`).join("")}</div></fieldset>
      <fieldset><legend>${esc(labels.select)}</legend>${stations.map(([id, number, city]) => `<label class="station-choice"><input type="checkbox" name="station" value="${esc(id)}" ${(!this._selected || this._selected.has(id)) ? "checked" : ""}><span>Packstation ${esc(number)} · ${esc(city)}<small class="station-fit"></small></span></label>`).join("")}</fieldset>
      <label class="notify">${esc(labels.notify)}<select name="notifier" aria-describedby="notify-hint"><option value="none">${esc(labels.inbox)}</option>${notifications.map(key => `<option value="${esc(key)}" ${draft?.get("notifier") === key ? "selected" : ""}>${esc(key.slice(11).replaceAll("_", " "))}</option>`).join("")}</select></label><p class="hint" id="notify-hint">${esc(labels.notifyHint)}</p>`}
      <button type="submit">${esc(state === "waiting" ? labels.stop : state === "matched" ? labels.reset : labels.start)}</button><p role="status"></p>
    </form></details>` : ""}
    <details class="map" ${mapOpen ? "open" : ""}><summary>${esc(labels.map)}</summary><div class="map-content">
      ${mapItems.length ? mapItems.map((item) =>
        `<div class="map-station"><strong>Packstation ${esc(item.meta.station_number)} · ${esc(item.meta.location_name || item.meta.city || item.meta.postal_code)}</strong>${directions(item, this._hass)}</div>`
      ).join("") : `<p>${esc(labels.coordinates)}</p>`}
    </div></details>`;
    const map = this.shadowRoot.querySelector(".map");
    const entities = mapItems.map(item => ({ entity: item.entities.free_total.entityId, name: `Packstation ${item.meta.station_number}`, label_mode: "state" }));
    map.addEventListener("toggle", () => {
      if (map.open) void this._openMap(entities);
    });
    if (map.open) void this._openMap(entities);
  }
}

if (!customElements.get("dhl-packstation-tools")) customElements.define("dhl-packstation-tools", PackstationTools);
