import { escapeHTML as esc, language, status } from "./data.js";

export const COPY = {
  de: {
    total: "Frei gesamt", week: "Wochentrend", weekInfo: "Typischer Tageswert aus den letzten 8 Wochen. Mindestens zwei beobachtete Tage je Wochentag.",
    missing: "Noch zu wenig Daten", few: "Wenige frei", many: "Viele frei", none: "Keine frei",
    alarm: "Paketalarm", map: "Karte öffnen", select: "Stationen", notify: "Benachrichtigung",
    inbox: "Home Assistant", start: "Suche starten", stop: "Suche stoppen", reset: "Neue Suche",
    waiting: "Warte auf passende Fächer", matched: "Passende Fächer gemeldet",
    error: "Aktion fehlgeschlagen. Prüfe Paketzahlen, Stationsauswahl und Benachrichtigung.",
    empty: "Wähle mindestens eine Station und gib eine Paketanzahl ein.",
    sizes: "Pakete pro Fachgröße", coordinates: "Noch keine Standortkoordinaten verfügbar.",
  },
  en: {
    total: "Total free", week: "Weekday trend", weekInfo: "Typical daily value over the last 8 weeks. At least two observed days per weekday.",
    missing: "Not enough data yet", few: "Few free", many: "Many free", none: "None free",
    alarm: "Package alarm", map: "Open map", select: "Stations", notify: "Notification",
    inbox: "Home Assistant", start: "Start search", stop: "Stop search", reset: "New search",
    waiting: "Waiting for matching compartments", matched: "Matching compartments reported",
    error: "Action failed. Check package counts, selected stations and notification.",
    empty: "Select at least one station and enter a package count.",
    sizes: "Packages by compartment size", coordinates: "No station coordinates available yet.",
  },
};

export function stationSummary(station, hass, showWeek) {
  const sensor = station.entities.free_total;
  if (!sensor) return "";
  const labels = COPY[language(hass)];
  const { latitude, longitude, week } = sensor.attributes;
  const href = mapLink(latitude, longitude);
  const total = status(station) === "fresh" && /^\d+$/.test(sensor.state) ? sensor.state : "–";
  const days = new Intl.DateTimeFormat(language(hass), { weekday: "short", timeZone: "UTC" });
  const trend = Array.isArray(week) && week.length === 7 ? week.map((day, index) => {
    const value = typeof day?.typical === "number" && Number.isFinite(day.typical) ? day.typical : null;
    const category = value === null ? "missing" : value >= 6 ? "many" : value > 0 ? "few" : "none";
    const number = value === null ? "–" : new Intl.NumberFormat(language(hass)).format(value);
    const name = days.format(new Date(Date.UTC(2026, 0, 5 + index)));
    return `<li class="${category}" aria-label="${esc(`${name}, ${labels[category]}, ${number}`)}"><span>${esc(name)}</span><span class="trend-value">${esc(number)}</span></li>`;
  }).join("") : "";
  return `<div class="station-summary"><span>${esc(labels.total)} <strong>${esc(total)}</strong></span>${href ? `<a href="${href}" target="_blank" rel="noopener noreferrer">${esc(labels.map)}</a>` : ""}</div>
    ${showWeek && trend ? `<section class="week"><h2>${esc(labels.week)}</h2><ul>${trend}</ul><p>${esc(labels.weekInfo)}</p></section>` : ""}`;
}

export function mapLink(lat, lon) {
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) return "";
  return `https://www.openstreetmap.org/?mlat=${lat}&amp;mlon=${lon}#map=17/${lat}/${lon}`;
}
