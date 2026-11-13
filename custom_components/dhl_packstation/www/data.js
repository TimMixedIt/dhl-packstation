export const SIZES = ["s", "m", "l", "xl"];

const translations = {
  de: {
    free: "Freie Fächer", overview: "Packstationen", sizes: "Fachgrößen:",
    many: "viele frei", none: "keine frei", unknown: "unbekannt", unit: "frei",
    updated: "Zuletzt aktualisiert", noTimestamp: "Kein DHL-Datenstand verfügbar",
    disclaimer: "Die tatsächliche Anzahl freier Fächer kann zum Zeitpunkt der Nutzung abweichen.",
    info: "Informationen zu freien Fächern", close: "Schließen",
    infoBody: "Die Fachzahlen stammen von DHL. Bei mehr als fünf freien Fächern zeigt diese Karte wie DHL „viele frei“. Im Karteneditor kannst du stattdessen genaue Zahlen wählen. Die Größe der gelben Fläche veranschaulicht die Fachgröße, nicht den Füllstand.",
    infoFreshness: "Fehlende, veraltete oder nicht erreichbare Daten gelten nicht als null freie Fächer. Die Altersgrenze legst du in den Optionen der Integration fest.",
    loading: "Packstationen werden geladen …", empty: "Noch keine Packstation eingerichtet.",
    missing: "Diese Packstation ist nicht verfügbar. Prüfe die Auswahl im Karteneditor.",
    fresh: "Aktuell", partial: "Teilweise Daten", stale: "Daten veraltet oder fehlend", offline: "Nicht erreichbar",
    station: "Packstation", title: "Titel", all: "Ohne Auswahl werden alle eingerichteten Stationen angezeigt.", exact: "Genaue Fachzahlen anzeigen", selection: "Stationen auswählen",
  },
  en: {
    free: "Free compartments", overview: "Packstations", sizes: "Compartment sizes:",
    many: "many free", none: "none free", unknown: "unknown", unit: "free",
    updated: "Last updated", noTimestamp: "No DHL observation timestamp available",
    disclaimer: "The actual number of free compartments may differ when you use the station.",
    info: "About free compartments", close: "Close",
    infoBody: "Counts are provided by DHL. Like DHL, this card shows “many free” above five compartments. Choose exact counts in the card editor if preferred. The height of the yellow shape illustrates compartment size, not occupancy.",
    infoFreshness: "Missing, stale, or unreachable data does not mean zero free compartments. Set the maximum data age in the integration options.",
    loading: "Loading Packstations …", empty: "No Packstation configured yet.",
    missing: "This Packstation is unavailable. Check the selection in the card editor.",
    fresh: "Current", partial: "Partial data", stale: "Data stale or missing", offline: "Unreachable",
    station: "Packstation", title: "Title", all: "Leave the selection empty to show all configured stations.", exact: "Show exact compartment counts", selection: "Select stations",
  },
};

export function language(hass) {
  return (hass?.locale?.language || hass?.language || "en").startsWith("de") ? "de" : "en";
}

export function text(hass) { return translations[language(hass)]; }

export function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

export function count(state) {
  if (!state || !/^\d+$/.test(state.state)) return null;
  const value = Number(state.state);
  return Number.isSafeInteger(value) ? value : null;
}

export function stations(hass) {
  const groups = new Map();
  for (const [entityId, state] of Object.entries(hass?.states || {})) {
    const attr = state.attributes || {};
    if (!attr.dhl_packstation_id || !attr.dhl_packstation_key) continue;
    const id = attr.dhl_packstation_id;
    if (!groups.has(id)) groups.set(id, { id, entities: {}, meta: attr });
    groups.get(id).entities[attr.dhl_packstation_key] = { ...state, entityId };
  }
  return [...groups.values()].sort((a, b) =>
    String(a.meta.postal_code).localeCompare(String(b.meta.postal_code)) ||
    Number(a.meta.station_number) - Number(b.meta.station_number));
}

export function status(station) {
  const state = station.entities.stale_data?.state;
  if (state === "unavailable") return "offline";
  if (state !== "off") return "stale";
  return SIZES.every((size) => count(station.entities[`free_${size}`]) !== null) ? "fresh" : "partial";
}

export function availableCount(station, size) {
  if (!["fresh", "partial"].includes(status(station))) return null;
  return count(station.entities[`free_${size}`]);
}

export function countLabel(value, exact, labels) {
  if (value === null) return labels.unknown;
  if (value === 0) return labels.none;
  return value > 5 && !exact ? labels.many : `${value} ${labels.unit}`;
}

export function timestamp(station, hass) {
  const raw = station.entities.source_timestamp?.state;
  if (!raw || !Number.isFinite(Date.parse(raw))) return null;
  const formatted = new Intl.DateTimeFormat(language(hass), {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
    timeZone: hass?.config?.time_zone || "Europe/Berlin",
  }).format(new Date(raw));
  return formatted + (language(hass) === "de" ? " Uhr" : "");
}

export function validateConfig(config, overview) {
  if (!config || typeof config !== "object") throw new Error("Card configuration is required");
  if (config.station !== undefined && (typeof config.station !== "string" || !config.station.trim())) throw new Error("station must be a station identifier");
  if (config.title !== undefined && typeof config.title !== "string") throw new Error("title must be text");
  if (config.show_exact !== undefined && typeof config.show_exact !== "boolean") throw new Error("show_exact must be true or false");
  if (overview && config.stations !== undefined && (!Array.isArray(config.stations) || config.stations.some((id) => typeof id !== "string" || !id.trim()))) throw new Error("stations must be a list of station identifiers");
  return { ...config };
}
