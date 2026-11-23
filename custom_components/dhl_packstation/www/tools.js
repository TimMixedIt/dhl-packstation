import { SIZES, escapeHTML as esc, language } from "./data.js";
import { COPY, coordinates, fitLabel, packageFit } from "./station-view.js";
import { alarmPanel, mapPanel, toolButton, toolsStyles } from "./tools-view.js";

class PackstationTools extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.shadowRoot.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-panel]");
      if (!button) return;
      this._activePanel = this._activePanel === button.dataset.panel ? null : button.dataset.panel;
      this._syncPanels();
    });
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

  update(hass, stations, all, config) {
    this._hass = hass;
    this._stations = stations;
    this._all = all;
    this._showAlarm = config.show_package_alarm !== false
      && hass?.user?.is_admin !== false
      && stations.length > 0
      && all.some(item => item.entities.free_total);
    this._showMap = config.show_station_map !== false;
    if (this._map) this._map.hass = hass;
    this._render();
    this._updateFit();
  }

  get demand() {
    if (!this._showAlarm) return {};
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
        this.shadowRoot.querySelector(".feedback").textContent = labels.empty;
        return;
      }
    }
    const button = event.submitter;
    if (button) button.disabled = true;
    try {
      await this._hass.callService("dhl_packstation", action, payload);
      const feedback = this.shadowRoot.querySelector(".feedback");
      if (feedback) feedback.textContent = "";
    } catch {
      const feedback = this.shadowRoot.querySelector(".feedback");
      if (feedback) feedback.textContent = labels.error;
    } finally {
      if (button) button.disabled = false;
    }
  }

  _syncPanels() {
    for (const button of this.shadowRoot.querySelectorAll(".tool")) {
      const open = this._activePanel === button.dataset.panel;
      button.setAttribute("aria-expanded", String(open));
      this.shadowRoot.getElementById(button.dataset.panel).hidden = !open;
    }
    if (this._activePanel === "map") void this._openMap();
  }

  async _openMap() {
    const container = this.shadowRoot.querySelector(".map-content");
    if (!container || this._map || container === this._mapTarget) return;
    this._mapTarget = container;
    const feedback = this.shadowRoot.querySelector(".map-feedback");
    const labels = COPY[language(this._hass)];
    const entities = this._mapEntities;
    feedback.hidden = false;
    feedback.textContent = labels.mapLoading;
    try {
      const helpers = await window.loadCardHelpers();
      if (container !== this.shadowRoot.querySelector(".map-content")) return;
      this._map = helpers.createCardElement({ type: "map", entities, auto_fit: true });
      this._map.hass = this._hass;
      container.append(this._map);
      feedback.hidden = true;
    } catch {
      if (this._mapTarget === container) {
        this._mapTarget = null;
        feedback.textContent = labels.mapError;
      }
    }
  }

  _render() {
    const labels = COPY[language(this._hass)];
    this._alarm = this._all.find((item) => item.entities.free_total?.attributes.alarm)?.entities.free_total.attributes.alarm ?? {};
    const mapItems = this._showMap ? this._stations.filter(coordinates) : [];
    const notifications = Object.keys(this._hass?.services?.notify || {}).filter((key) => key.startsWith("mobile_app_")).sort();
    const stations = this._stations.map((item) => [item.id, item.meta.station_number, item.meta.city || item.meta.postal_code]);
    const locations = JSON.stringify(mapItems.map(item => [
      item.entities.free_total.entityId, item.meta.station_number, item.meta.location_name, coordinates(item),
    ]));
    const signature = JSON.stringify([labels.alarm, this._alarm, stations, notifications, locations, this._showAlarm, this._showMap]);
    if (signature === this._signature) return;
    this._signature = signature;
    if ((this._activePanel === "alarm" && !this._showAlarm) || (this._activePanel === "map" && !this._showMap)) this._activePanel = null;
    const previous = this.shadowRoot.querySelector("form");
    const draft = previous ? new FormData(previous) : null;
    const state = ["waiting", "matched"].includes(this._alarm.status) ? this._alarm.status : null;
    const badge = state && (state === "waiting" ? labels.searchRunning : labels.searchMatched);
    const match = this._all.find((item) => item.id === this._alarm.match);
    const requested = SIZES.filter(size => this._alarm.sizes?.[size]).map(size => `${this._alarm.sizes[size]}× ${size.toUpperCase()}`).join(" · ");
    const focused = this.shadowRoot.activeElement?.dataset.panel;
    this._mapTarget = null;
    this.hidden = !this._showAlarm && !this._showMap;
    this.shadowRoot.innerHTML = this.hidden ? toolsStyles : `${toolsStyles}
      <div class="toolbar" role="group" aria-label="${esc(labels.tools)}">
        ${this._showAlarm ? toolButton("alarm", labels.alarm, "mdi:bell-outline", badge) : ""}
        ${this._showMap ? toolButton("map", labels.map, "mdi:map-outline") : ""}
      </div>
      ${this._showAlarm ? alarmPanel(labels, { state, requested, match, stations, selected: this._selected, draft, notifications }) : ""}
      ${this._showMap ? mapPanel(labels, mapItems, this._hass) : ""}`;
    this._mapEntities = mapItems.map(item => ({ entity: item.entities.free_total.entityId, name: `Packstation ${item.meta.station_number}`, label_mode: "state" }));
    if (locations === this._locations && this._map) this.shadowRoot.querySelector(".map-content")?.append(this._map);
    else this._map = null;
    this._locations = locations;
    this._syncPanels();
    if (focused) this.shadowRoot.querySelector(`button[data-panel="${focused}"]`)?.focus({ preventScroll: true });
  }
}

if (!customElements.get("dhl-packstation-tools")) customElements.define("dhl-packstation-tools", PackstationTools);
