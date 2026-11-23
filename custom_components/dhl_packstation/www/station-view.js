import { escapeHTML as esc, language, status, SIZES, availableCount } from "./data.js";

const WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

export const COPY = {
  de: {
    total: "Frei gesamt", week: "Wochentrend", weekInfo: "Eigene Messungen: typischer Tageswert aus bis zu 8 Wochen. Mindestens zwei beobachtete Tage je Wochentag.",
    forecast: "DHL-Auslastung nach Wochentag", forecastInfo: "1 niedrig · 2 mittel · 3 hoch",
    forecastLevels: ["Keine Angabe", "Niedrige Auslastung", "Mittlere Auslastung", "Hohe Auslastung"],
    missing: "Noch zu wenig Daten", few: "Wenige frei", many: "Viele frei", none: "Keine frei",
    alarm: "Paketalarm", map: "Standorte auf der Karte", select: "Stationen", notify: "Benachrichtigung",
    inbox: "HA-Glocke (ohne Push)", notifyHint: "Wähle ein Gerät für eine Push-Nachricht.", apple: "Apple Karten",
    fits: "Passt", noData: "Daten fehlen", shortage: "Fehlt", stationCol: "Station", comparison: "Freie Fächer im Vergleich",
    matches: (count, total) => `${count} von ${total} Stationen passen`, start: "Suche starten", stop: "Suche stoppen", reset: "Neue Suche",
    waiting: "Warte auf passende Fächer", matched: "Passende Fächer gemeldet",
    error: "Aktion fehlgeschlagen. Prüfe Paketzahlen, Stationsauswahl und Benachrichtigung.",
    empty: "Wähle mindestens eine Station und gib eine Paketanzahl ein.",
    sizes: "Pakete pro Fachgröße", coordinates: "Noch keine Standortkoordinaten verfügbar.",
  },
  en: {
    total: "Total free", week: "Weekday trend", weekInfo: "Local observations: typical daily value over up to 8 weeks. At least two observed days per weekday.",
    forecast: "DHL utilization by weekday", forecastInfo: "1 low · 2 medium · 3 high",
    forecastLevels: ["No estimate", "Low utilization", "Medium utilization", "High utilization"],
    missing: "Not enough data yet", few: "Few free", many: "Many free", none: "None free",
    alarm: "Package alarm", map: "Station map", select: "Stations", notify: "Notification",
    inbox: "HA inbox (no push)", notifyHint: "Choose a device to receive a push notification.", apple: "Apple Maps",
    fits: "Fits", noData: "Data missing", shortage: "Missing", stationCol: "Station", comparison: "Compare free compartments",
    matches: (count, total) => `${count} of ${total} stations fit`, start: "Start search", stop: "Stop search", reset: "New search",
    waiting: "Waiting for matching compartments", matched: "Matching compartments reported",
    error: "Action failed. Check package counts, selected stations and notification.",
    empty: "Select at least one station and enter a package count.",
    sizes: "Packages by compartment size", coordinates: "No station coordinates available yet.",
  },
};

export function stationSummary(station, hass, showLocalTrend) {
  const sensor = station.entities.free_total;
  const labels = COPY[language(hass)];
  const week = sensor?.attributes?.week;
  const forecast = station.entities.source_timestamp?.attributes?.dhl_weekday_utilization;
  const total = status(station) === "fresh" && /^\d+$/.test(sensor?.state) ? sensor.state : "–";
  const days = new Intl.DateTimeFormat(language(hass), { weekday: "short", timeZone: "UTC" });
  const dayLabel = index => days.format(new Date(Date.UTC(2026, 0, 5 + index)));
  const levels = WEEKDAYS.map(day => forecast?.[day]);
  let weekly = "";
  if (levels.some(level => [1, 2, 3].includes(level))) {
    const cells = levels.map((level, index) => {
      const valid = [1, 2, 3].includes(level);
      const name = dayLabel(index);
      return `<li class="${valid ? `level-${level}` : "missing"}" aria-label="${esc(`${name}, ${labels.forecastLevels[valid ? level : 0]}`)}"><span>${esc(name)}</span><span class="trend-value">${valid ? level : "–"}</span></li>`;
    }).join("");
    weekly = `<section class="week forecast"><h2>${esc(labels.forecast)}</h2><ul>${cells}</ul><p>${esc(labels.forecastInfo)}</p></section>`;
  } else if (showLocalTrend && Array.isArray(week) && week.length === WEEKDAYS.length) {
    const cells = week.map((day, index) => {
      const value = typeof day?.typical === "number" && Number.isFinite(day.typical) ? day.typical : null;
      const category = value === null ? "missing" : value >= 6 ? "many" : value > 0 ? "few" : "none";
      const number = value === null ? "–" : new Intl.NumberFormat(language(hass)).format(value);
      const name = dayLabel(index);
      return `<li class="${category}" aria-label="${esc(`${name}, ${labels[category]}, ${number}`)}"><span>${esc(name)}</span><span class="trend-value">${esc(number)}</span></li>`;
    }).join("");
    weekly = `<section class="week"><h2>${esc(labels.week)}</h2><ul>${cells}</ul><p>${esc(labels.weekInfo)}</p></section>`;
  }
  return `${sensor ? `<div class="station-summary"><span>${esc(labels.total)} <strong>${esc(total)}</strong></span>${directions(station, hass)}</div>` : ""}${weekly}`;
}

export function coordinates(station) {
  const { latitude: lat, longitude: lon } = station.entities.free_total?.attributes ?? {};
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
  return `${lat},${lon}`;
}

export function directions(station, hass) {
  const point = coordinates(station);
  if (!point) return "";
  const name = `Packstation ${station.meta.station_number}`;
  const destination = encodeURIComponent(point);
  const links = [
    [COPY[language(hass)].apple, `https://maps.apple.com/directions?destination=${destination}`],
    ["Google Maps", `https://www.google.com/maps/dir/?api=1&destination=${destination}`],
  ];
  return `<span class="directions">${links.map(([label, url]) => `<a href="${esc(url)}" aria-label="${esc(`${label} · ${name}`)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`).join("")}</span>`;
}

export function packageFit(station, demand) {
  const needed = SIZES.filter(size => Number.isInteger(demand[size]) && demand[size] > 0);
  if (!needed.length) return null;
  const counts = needed.map(size => [size, availableCount(station, size)]);
  const shortages = counts.filter(([size, count]) => count !== null && count < demand[size])
    .map(([size, count]) => `${demand[size] - count}× ${size.toUpperCase()}`);
  if (shortages.length) return { state: "shortage", shortages };
  return { state: counts.some(([, count]) => count === null) ? "noData" : "fits" };
}

export function fitLabel(fit, copy) {
  if (!fit) return "";
  return fit.shortages ? `${copy.shortage} ${fit.shortages.join(", ")}` : copy[fit.state];
}
