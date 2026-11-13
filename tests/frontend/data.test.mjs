import { test } from "node:test";
import assert from "node:assert/strict";
import { SIZES, availableCount, count, countLabel, escapeHTML, language, stations, status, text, timestamp, validateConfig } from "../../custom_components/dhl_packstation/www/data.js";
import { overviewView, singleView } from "../../custom_components/dhl_packstation/www/view.js";

const hass = { locale: { language: "de" }, config: { time_zone: "Europe/Berlin" }, states: {} };
function fixture() {
  const entities = Object.fromEntries(SIZES.map((size, index) => [`free_${size}`, { state: String([17, 4, 7, 1][index]), entityId: `sensor.renamed_${size}` }]));
  return { id: "1-67141189", meta: { station_number: "189", postal_code: "67141", city: "Neuhofen", address: "Industriestr. 10" }, entities: { ...entities, source_timestamp: { state: "2026-11-12T23:28:03+00:00" }, stale_data: { state: "off" } } };
}

test("only nonnegative safe integer states become counts", () => {
  for (const raw of ["unknown", "unavailable", "", " ", "-1", "2.5", "1e2", "Infinity", "9007199254740992"]) assert.equal(count({ state: raw }), null);
  assert.equal(count(undefined), null);
  assert.equal(count({ state: "0" }), 0);
  assert.equal(count({ state: "17" }), 17);
});

test("DHL-style labels retain the optional exact number and real zero", () => {
  const labels = text(hass);
  assert.equal(countLabel(6, false, labels), "viele frei");
  assert.equal(countLabel(6, true, labels), "6 frei");
  assert.equal(countLabel(5, false, labels), "5 frei");
  assert.equal(countLabel(0, false, labels), "keine frei");
  assert.equal(countLabel(null, false, labels), "unbekannt");
});

test("grouping uses stable attributes instead of translated or renamed entity IDs", () => {
  const data = { states: { "sensor.custom_name": { state: "3", attributes: { dhl_packstation_id: "1-67141189", dhl_packstation_key: "free_s", postal_code: "67141", station_number: "189" } }, "sensor.unrelated": { state: "99", attributes: {} } } };
  const grouped = stations(data);
  assert.equal(grouped.length, 1);
  assert.equal(grouped[0].entities.free_s.entityId, "sensor.custom_name");
  assert.deepEqual(stations(undefined), []);
});

test("stale and unreachable stations never show retained counts as available", () => {
  const station = fixture();
  assert.equal(status(station), "fresh");
  station.entities.free_m.state = "unknown";
  assert.equal(status(station), "partial");
  assert.equal(availableCount(station, "s"), 17);
  for (const raw of ["on", "unknown", "unavailable"]) {
    station.entities.stale_data.state = raw;
    assert.equal(availableCount(station, "s"), null);
  }
  assert.equal(status(station), "offline");
});

test("timestamps use the configured zone and invalid values remain unknown", () => {
  const station = fixture();
  assert.match(timestamp(station, hass), /13\.11\.2026, 00:28 Uhr/);
  station.entities.source_timestamp.state = "unavailable";
  assert.equal(timestamp(station, hass), null);
  assert.equal(language({ language: "de-DE" }), "de");
  assert.equal(language(undefined), "en");
});

test("configuration validation rejects malformed inputs", () => {
  for (const input of [null, { station: 1 }, { station: "" }, { title: {} }, { show_exact: "false" }, { stations: "all" }, { stations: [null] }]) assert.throws(() => validateConfig(input, true));
  assert.deepEqual(validateConfig({ type: "custom:dhl-packstation-card" }, false), { type: "custom:dhl-packstation-card" });
});

test("all data interpolated into HTML is escaped", () => {
  assert.equal(escapeHTML('<img src=x onerror="bad()">&\''), "&lt;img src=x onerror=&quot;bad()&quot;&gt;&amp;&#39;");
  const station = fixture();
  station.meta.city = '<script>alert("x")</script>';
  station.meta.station_number = '"><img src=x>';
  const html = overviewView([station], {}, hass) + singleView(station, {}, hass);
  assert.ok(!html.includes("<script>"));
  assert.ok(!html.includes("<img"));
});
