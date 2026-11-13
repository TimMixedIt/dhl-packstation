import { escapeHTML as esc, stations, text, validateConfig } from "./data.js";
import { styles } from "./styles.js";
import { chevron, helpDialog, locker, overviewView, singleView } from "./view.js";
import "./editor.js";

class PackstationCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._expanded = true;
    this.shadowRoot.addEventListener("click", (event) => this._click(event));
    this.shadowRoot.addEventListener("toggle", (event) => {
      if (event.target.tagName === "DETAILS") this._expanded = event.target.open;
    }, true);
  }

  static getConfigElement() { return document.createElement("dhl-packstation-card-editor"); }
  static getStubConfig(hass) {
    const station = stations(hass)[0];
    return station ? { station: station.id } : {};
  }
  get overview() { return false; }
  getCardSize() { return this.overview ? 3 + (this._items?.length || 1) * 2 : 6; }
  getGridOptions() { return { columns: 12, rows: "auto", min_columns: 6 }; }

  setConfig(config) { this._config = validateConfig(config, this.overview); this._render(); }
  set hass(hass) { this._hass = hass; this._render(); }

  _click(event) {
    const button = event.target.closest?.("button[data-action]");
    if (!button) return;
    if (button.dataset.action === "info") this.shadowRoot.querySelector("dialog").showModal();
    if (button.dataset.action === "close") this.shadowRoot.querySelector("dialog").close();
    if (button.dataset.action === "more-info" && button.dataset.entity) this.dispatchEvent(new CustomEvent("hass-more-info", {
      detail: { entityId: button.dataset.entity }, bubbles: true, composed: true,
    }));
  }

  _render() {
    if (!this._config) return;
    const labels = text(this._hass), all = stations(this._hass);
    this._items = this.overview
      ? all.filter((item) => !this._config.stations?.length || this._config.stations.includes(item.id))
      : all.filter((item) => item.id === (this._config.station || all[0]?.id));
    let body;
    if (!this._items.length) {
      const message = !this._hass ? labels.loading : all.length ? labels.missing : labels.empty;
      body = `<p class="empty-message" role="status">${esc(message)}</p>`;
    } else {
      body = this.overview ? overviewView(this._items, this._config, this._hass) : singleView(this._items[0], this._config, this._hass);
    }
    const title = this._config.title || (this.overview ? labels.overview : labels.free);
    const html = `<style>${styles}</style><ha-card><details open><summary>${locker}<span>${esc(title)}</span>${chevron}</summary>${body}</details>${helpDialog(this._hass)}</ha-card>`;
    if (html === this._html) return;
    const dialogOpen = this.shadowRoot.querySelector("dialog")?.open;
    const summaryFocused = this.shadowRoot.activeElement?.tagName === "SUMMARY";
    const focused = this.shadowRoot.activeElement?.dataset;
    this._html = html;
    this.shadowRoot.innerHTML = html;
    this.shadowRoot.querySelector("details").open = this._expanded;
    if (dialogOpen) this.shadowRoot.querySelector("dialog").showModal();
    else if (summaryFocused) this.shadowRoot.querySelector("summary").focus({ preventScroll: true });
    else if (focused?.action) {
      const button = [...this.shadowRoot.querySelectorAll("button")].find((item) => item.dataset.action === focused.action && item.dataset.entity === focused.entity);
      button?.focus({ preventScroll: true });
    }
  }
}

class PackstationOverviewCard extends PackstationCard {
  get overview() { return true; }
  static getStubConfig() { return {}; }
}

if (!customElements.get("dhl-packstation-card")) customElements.define("dhl-packstation-card", PackstationCard);
if (!customElements.get("dhl-packstation-overview-card")) customElements.define("dhl-packstation-overview-card", PackstationOverviewCard);
window.customCards = window.customCards || [];
for (const card of [
  { type: "dhl-packstation-card", name: "DHL Packstation · Freie Fächer", description: "Eine Packstation mit S/M/L/XL im DHL-Stil.", preview: true },
  { type: "dhl-packstation-overview-card", name: "DHL Packstation · Mehrere Stationen", description: "Freie Fächer mehrerer Packstationen vergleichen.", preview: true },
]) {
  if (!window.customCards.some((item) => item.type === card.type)) window.customCards.push({ ...card, documentationURL: "https://github.com/TimMixedIt/dhl-packstation#dashboard-cards" });
}
