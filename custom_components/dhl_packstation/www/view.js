import { COPY, stationSummary } from "./station-view.js";
import { SIZES, availableCount, countLabel, escapeHTML as esc, language, status, text, timestamp } from "./data.js";

const icon = (body, cls = "") => `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${body}</svg>`;
export const locker = icon('<path fill="currentColor" d="M2 3h20v2H2zm1 4h5v4H3zm7 0h5v10h-5zm7 0h4v4h-4zM3 13h5v4H3zm14 0h4v4h-4zM3 19h5v3H3zm7 0h5v3h-5zm7 0h4v3h-4z"/>', "locker");
export const chevron = icon('<path d="m6 9 6 6 6-6" fill="none" stroke="currentColor" stroke-width="2"/>', "chevron");
const info = icon('<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M11 10h2v8h-2zm0-4h2v2h-2z" fill="currentColor"/>');

function stateIcon(value) {
  if (value > 0) return icon('<circle cx="12" cy="12" r="11" fill="currentColor"/><path d="m6 12 4 4 8-9" fill="none" stroke="#1b2411" stroke-width="2.5"/>', "state-icon yes");
  return icon(`<circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>${value === null ? '<path d="M9 8a3 3 0 0 1 6 0c0 3-3 2-3 5m0 3v1" fill="none" stroke="currentColor" stroke-width="2"/>' : '<path d="M7 12h10" stroke="currentColor" stroke-width="2"/>'}`, "state-icon neutral");
}

function compartment(station, size, config, labels) {
  const value = availableCount(station, size);
  const entity = station.entities[`free_${size}`]?.entityId;
  const label = countLabel(value, config.show_exact, labels);
  const stateClass = value === null ? "unknown" : value === 0 ? "empty" : "available";
  return `<button class="tile ${stateClass}" data-action="more-info" data-entity="${esc(entity)}" ${entity ? "" : "disabled"} aria-label="${esc(`${size.toUpperCase()} ${label}, ${labels.station} ${station.meta.station_number}`)}">${stateIcon(value)}<span class="shape-space"><span class="shape ${size}">${size.toUpperCase()}</span></span> <span class="count">${esc(label)}</span></button>`;
}

function updated(station, hass) {
  const labels = text(hass), date = timestamp(station, hass);
  return `<div class="timestamp">${esc(date ? `${labels.updated}: ${date}` : labels.noTimestamp)}</div>`;
}

export function singleView(station, config, hass) {
  const labels = text(hass), state = status(station);
  return `<div class="body">
    ${state === "fresh" ? "" : `<p class="warning" role="status">${esc(labels[state])}</p>`}
    <div class="sizes-header"><h2>${esc(labels.sizes)}</h2><button class="info" data-action="info" aria-label="${esc(labels.info)}">${info}</button></div>
    <div class="grid">${SIZES.map((size) => compartment(station, size, config, labels)).join("")}</div>
    ${updated(station, hass)}${stationSummary(station, hass, true)}<p class="note">${esc(labels.disclaimer)}</p>
  </div>`;
}

export function overviewView(items, config, hass, expanded = new Set()) {
  const labels = text(hass), copy = COPY[language(hass)];
  return `<div class="overview">
    <div class="compare" role="region" aria-label="${esc(copy.comparison)}">
      <p class="compare-result" role="status" hidden></p>
      <div class="compare-row compare-head"><span>${esc(copy.stationCol)}</span>${SIZES.map(size => `<span>${size.toUpperCase()}</span>`).join("")}</div>
      ${items.map((station, index) => {
        const state = status(station), meta = station.meta;
        const name = `${labels.station} ${meta.station_number}`;
        const open = expanded.has(station.id);
        const total = station.entities.free_total?.state;
        const label = state === "fresh" && /^\d+$/.test(total ?? "") ? `${total} ${labels.unit}` : labels[state];
        const counts = SIZES.map(size => {
          const value = availableCount(station, size);
          const entity = station.entities[`free_${size}`]?.entityId;
          const displayed = value === null ? "–" : value > 5 && !config.show_exact ? "6+" : value;
          return `<button class="metric ${value > 0 ? "available" : value === null ? "unknown" : "empty"}" data-action="more-info" data-entity="${esc(entity)}" aria-label="${esc(`${displayed} · ${size.toUpperCase()}, ${name}, ${countLabel(value, true, labels)}`)}" ${entity ? "" : "disabled"}>${displayed}</button>`;
        }).join("");
        return `<section class="station" aria-label="${esc(name)}">
          <div class="compare-row"><button type="button" class="station-toggle" data-action="station-details" data-entity="${esc(station.id)}" aria-expanded="${open}" aria-controls="station-${index}">
            <span class="station-name">${esc([meta.station_number, meta.location_name || meta.city || labels.station].join(" · "))}</span>
            <span class="compare-label ${state}" data-default="${esc(label)}" data-state="${state}">${esc(label)}</span>
          </button>${counts}</div>
          <div class="station-detail" id="station-${index}" ${open ? "" : "hidden"}>
            <p class="address">${esc([name, meta.address, [meta.postal_code, meta.city].filter(Boolean).join(" ")].filter(Boolean).join(" · "))}</p>
            ${updated(station, hass)}${stationSummary(station, hass, false)}
          </div>
        </section>`;
      }).join("")}
    </div><p class="note">${esc(labels.disclaimer)}</p>
  </div>`;
}

export function helpDialog(hass) {
  const labels = text(hass);
  return `<dialog aria-labelledby="help-title"><h2 id="help-title">${esc(labels.info)}</h2><p>${esc(labels.infoBody)}</p><p>${esc(labels.infoFreshness)}</p><button class="close" data-action="close">${esc(labels.close)}</button></dialog>`;
}
