import { SIZES, escapeHTML as esc } from "./data.js";
import { directions } from "./station-view.js";

export const toolsStyles = `<style>
  :host { display:block; color:var(--primary-text-color,#222); font:inherit; }
  :host([hidden]) { display:none; }
  [hidden] { display:none !important; }
  button,input,select { font:inherit; color:inherit; }
  :focus-visible { outline:2px solid var(--primary-color,#03a9f4); outline-offset:2px; }
  .toolbar { display:flex; flex-wrap:wrap; gap:8px; }
  .tool { display:inline-flex; align-items:center; justify-content:center; gap:7px; min-height:44px; flex:1 1 auto; padding:6px 10px; cursor:pointer; font-size:13px; font-weight:650; text-align:left; background:none; border:1px solid var(--divider-color,#888); border-radius:10px; }
  .tool[aria-expanded="true"] { background:var(--secondary-background-color,#e9edf0); border-color:var(--secondary-text-color,#777); }
  ha-icon { flex:none; --mdc-icon-size:17px; color:var(--secondary-text-color,#666); }
  .tool-label { display:grid; gap:1px; }
  .tool-state { font-size:11px; font-weight:500; color:var(--secondary-text-color,#666); }
  .panel { margin-top:8px; padding:12px; border-radius:12px; background:var(--secondary-background-color,#f3f4f6); }
  form { display:grid; gap:12px; }
  fieldset { min-width:0; margin:0; padding:0; border:0; }
  legend,.field-title { font-size:13px; font-weight:650; line-height:1.4; padding:0; margin-bottom:6px; }
  .pack-counts { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:6px; }
  .pack-counts label { display:grid; gap:4px; text-align:center; font-size:12px; font-weight:650; }
  input[type=number],select { box-sizing:border-box; width:100%; min-width:0; min-height:44px; background:var(--card-background-color,#fff); border:1px solid var(--divider-color,#888); border-radius:8px; padding:6px; font-size:16px; }
  input[type=number] { appearance:textfield; text-align:center; font-weight:700; font-variant-numeric:tabular-nums; }
  input[type=number]::-webkit-inner-spin-button { appearance:none; }
  select { appearance:none; padding:6px 32px 6px 10px; text-overflow:ellipsis; }
  .select-wrap { position:relative; }
  .select-wrap::after { content:""; position:absolute; right:14px; top:17px; width:7px; height:7px; border:solid currentColor; border-width:0 1.5px 1.5px 0; transform:rotate(45deg); pointer-events:none; }
  .station-list,.routes { margin:0; padding:0; list-style:none; border-top:1px solid var(--divider-color,#888); }
  .station-list li,.routes li { border-bottom:1px solid var(--divider-color,#888); }
  .station-choice { display:flex; align-items:center; gap:8px; min-height:44px; padding-block:4px; cursor:pointer; }
  .station-choice input { flex:none; margin:0; width:18px; height:18px; accent-color:#fbd443; }
  .station-caption { flex:1; min-width:0; font-size:13px; overflow-wrap:anywhere; }
  .station-fit { display:block; font-size:12px; color:var(--secondary-text-color,#666); }
  .station-fit:empty { display:none; }
  .station-fit.fits { font-weight:700; color:var(--primary-text-color,#222); }
  .notify { display:grid; min-width:0; }
  .hint,.feedback,.map-feedback { margin:4px 0 0; color:var(--secondary-text-color,#666); font-size:12px; }
  .feedback:empty { display:none; }
  .submit { justify-self:start; min-height:44px; padding:6px 14px; border:1px solid transparent; border-radius:8px; cursor:pointer; background:#fbd443; color:#171717; font-size:14px; font-weight:700; }
  .submit.secondary { color:inherit; background:var(--card-background-color,#fff); border-color:var(--divider-color,#888); }
  .submit:disabled { opacity:.6; cursor:wait; }
  .alarm-status { display:grid; gap:4px; font-size:13px; margin:0; }
  .alarm-status span { color:var(--secondary-text-color,#666); }
  .map-content > ha-card,.map-content > hui-map-card { --ha-card-border-width:0px; --ha-card-box-shadow:none; display:block; }
  .map-content:not(:empty) { border-radius:8px; overflow:hidden; }
  .routes { margin-top:12px; }
  .routes li { padding:8px 0; font-size:13px; overflow-wrap:anywhere; }
  .routes li:last-child { border-bottom:0; padding-bottom:0; }
  .directions { display:flex; flex-wrap:wrap; gap:4px 8px; margin-top:4px; }
  .directions a { display:inline-flex; align-items:center; min-height:28px; padding:0 8px; border:1px solid var(--divider-color,#888); border-radius:6px; font-size:12px; color:var(--primary-text-color,#222); }
  @media (forced-colors:active) { input[type=number],select,.tool,.submit { border-color:ButtonText; } }
</style>`;

export function toolButton(id, label, icon, status) {
  return `<button type="button" class="tool" data-panel="${id}" aria-expanded="false" aria-controls="${id}">
    <ha-icon icon="${icon}" aria-hidden="true"></ha-icon>
    <span class="tool-label"><span>${esc(label)}</span>${status ? `<span class="tool-state">${esc(status)}</span>` : ""}</span>
  </button>`;
}

export function alarmPanel(labels, { state, requested, match, stations, selected, draft, notifications }) {
  return `<section id="alarm" class="panel alarm" aria-label="${esc(labels.alarm)}" hidden><form>
    ${state ? `<p class="alarm-status"><strong>${esc(labels[state])}</strong><span>${esc(requested)}${match ? ` · Packstation ${esc(match.meta.station_number)}` : ""}</span></p>` : `
    <fieldset><legend>${esc(labels.sizes)}</legend><div class="pack-counts">
      ${SIZES.map(size => `<label>${size.toUpperCase()}<input type="number" inputmode="numeric" min="0" max="99" step="1" name="${size}" value="${esc(draft?.get(size) ?? 0)}"></label>`).join("")}
    </div></fieldset>
    <fieldset><legend>${esc(labels.select)}</legend><ul class="station-list">
      ${stations.map(([id, number, city]) => `<li><label class="station-choice"><input type="checkbox" name="station" value="${esc(id)}" ${(!selected || selected.has(id)) ? "checked" : ""}><span class="station-caption">Packstation ${esc(number)} · ${esc(city)}<small class="station-fit"></small></span></label></li>`).join("")}
    </ul></fieldset>
    <div class="notify"><label class="field-title" for="alarm-notifier">${esc(labels.notify)}</label><div class="select-wrap"><select id="alarm-notifier" name="notifier" aria-describedby="notify-hint">
      <option value="none">${esc(labels.inbox)}</option>
      ${notifications.map(key => `<option value="${esc(key)}" ${draft?.get("notifier") === key ? "selected" : ""}>${esc(key.slice(11).replaceAll("_", " "))}</option>`).join("")}
    </select></div><p class="hint" id="notify-hint">${esc(labels.notifyHint)}</p></div>`}
    <button type="submit" class="submit ${state === "waiting" ? "secondary" : ""}">${esc(state === "waiting" ? labels.stop : state === "matched" ? labels.reset : labels.start)}</button>
    <p class="feedback" role="status"></p>
  </form></section>`;
}

export function mapPanel(labels, stations, hass) {
  return `<section id="map" class="panel map" aria-label="${esc(labels.map)}" hidden>
    ${stations.length ? `<div class="map-content"></div><p class="map-feedback" role="status" hidden></p><ul class="routes">
      ${stations.map(item => `<li><strong>Packstation ${esc(item.meta.station_number)} · ${esc(item.meta.location_name || item.meta.city || item.meta.postal_code)}</strong>${directions(item, hass)}</li>`).join("")}
    </ul>` : `<p class="map-feedback">${esc(labels.coordinates)}</p>`}
  </section>`;
}
