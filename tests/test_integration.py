"""Test setup, entities, expiry, polling, errors, and unloading together."""

from copy import deepcopy
from datetime import timedelta

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.translation import async_get_translations
from homeassistant.util import dt as dt_util

from custom_components.dhl_packstation.const import API_BASE, DOMAIN

from .conftest import DETAIL_URL, MockConfigEntry, async_fire_time_changed


def entity_id(hass, key, station="1-67141189", domain="sensor"):
    return er.async_get(hass).async_get_entity_id(domain, DOMAIN, f"{station}_{key}")


async def setup(hass, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED


async def test_setup_entities(hass, entry, mock_dhl):
    await setup(hass, entry)
    assert len(er.async_get(hass).entities) == 6
    assert mock_dhl.call_count == 1
    for size, count in {"s": 9, "m": 10, "l": 8, "xl": 1}.items():
        assert hass.states.get(entity_id(hass, f"free_{size}")).state == str(count)
    assert (
        hass.states.get(entity_id(hass, "stale_data", domain="binary_sensor")).state
        == "off"
    )
    assert (
        hass.states.get(entity_id(hass, "source_timestamp")).state
        == "2026-11-12T23:58:00+00:00"
    )
    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, "1-67141189"), entry.entry_id
    )
    assert device is not None
    assert device.manufacturer == "DHL"


async def test_german_names_and_unit_translation(hass, entry, mock_dhl):
    hass.config.language = "de"
    await setup(hass, entry)
    state = hass.states.get(entity_id(hass, "free_s"))
    assert state.attributes["unit_of_measurement"] == "compartments"
    assert "Freie Fächer S" in state.name
    translations = await async_get_translations(hass, "de", "entity", {DOMAIN})
    assert (
        translations[
            "component.dhl_packstation.entity.sensor.free_s.unit_of_measurement"
        ]
        == "Fächer"
    )


async def test_expiry_without_http_and_recovery(
    hass, entry, mock_dhl, station, freezer
):
    await setup(hass, entry)
    coordinator = entry.runtime_data
    coordinator._unschedule_refresh()
    now = dt_util.utcnow() + timedelta(minutes=58)
    freezer.move_to(now)
    async_fire_time_changed(hass, now)
    await hass.async_block_till_done()
    assert mock_dhl.call_count == 1
    for size in ("s", "m", "l", "xl"):
        assert hass.states.get(entity_id(hass, f"free_{size}")).state == "unavailable"
    assert (
        hass.states.get(entity_id(hass, "stale_data", domain="binary_sensor")).state
        == "on"
    )
    assert hass.states.get(entity_id(hass, "source_timestamp")).state != "unavailable"
    mock_dhl.clear_requests()
    station["liveStatus"]["sourceTimestamp"] = now.isoformat()
    station["liveStatus"]["freeCompartmentsS"] = 0
    mock_dhl.get(DETAIL_URL, json=station)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id(hass, "free_s")).state == "0"
    assert (
        hass.states.get(entity_id(hass, "stale_data", domain="binary_sensor")).state
        == "off"
    )


async def test_poll_once_for_all_entities(hass, entry, mock_dhl, freezer):
    await setup(hass, entry)
    now = dt_util.utcnow() + timedelta(minutes=16)
    freezer.move_to(now)
    async_fire_time_changed(hass, now)
    await hass.async_block_till_done()
    assert mock_dhl.call_count == 2


async def test_update_failure_then_recovery(hass, entry, mock_dhl, station):
    await setup(hass, entry)
    mock_dhl.clear_requests()
    mock_dhl.get(DETAIL_URL, status=503)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    for state in hass.states.async_all():
        if state.entity_id.startswith(("sensor.", "binary_sensor.")):
            assert state.state == "unavailable"
    mock_dhl.clear_requests()
    mock_dhl.get(DETAIL_URL, json=station)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id(hass, "free_s")).state == "9"


@pytest.mark.parametrize(
    "live",
    [None, {}, {"sourceTimestamp": "2026-11-12T20:00:00Z", "freeCompartmentsS": 4}],
)
async def test_no_current_data_is_not_zero(hass, entry, aioclient_mock, station, live):
    station["liveStatus"] = live
    aioclient_mock.get(DETAIL_URL, json=station)
    await setup(hass, entry)
    assert hass.states.get(entity_id(hass, "free_s")).state == "unavailable"
    assert (
        hass.states.get(entity_id(hass, "stale_data", domain="binary_sensor")).state
        == "on"
    )


async def test_one_invalid_size_leaves_other_sizes(
    hass, entry, aioclient_mock, station
):
    station["liveStatus"]["freeCompartmentsS"] = -1
    aioclient_mock.get(DETAIL_URL, json=station)
    await setup(hass, entry)
    assert hass.states.get(entity_id(hass, "free_s")).state == "unavailable"
    assert hass.states.get(entity_id(hass, "free_m")).state == "10"


async def test_setup_failure_retries(hass, entry, aioclient_mock):
    aioclient_mock.get(DETAIL_URL, status=503)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_rate_limit_backoff(hass, entry, mock_dhl):
    await setup(hass, entry)
    mock_dhl.clear_requests()
    mock_dhl.get(DETAIL_URL, status=429, headers={"Retry-After": "3600"})
    await entry.runtime_data.async_refresh()
    assert entry.runtime_data.last_exception.retry_after == 3600
    assert not entry.runtime_data.last_update_success


async def test_unload_cancels_poll_and_expiry(hass, entry, mock_dhl, freezer):
    await setup(hass, entry)
    coordinator = entry.runtime_data
    assert coordinator._cancel_expiry is not None
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert coordinator._cancel_expiry is None
    now = dt_util.utcnow() + timedelta(hours=2)
    freezer.move_to(now)
    async_fire_time_changed(hass, now)
    await hass.async_block_till_done()
    assert mock_dhl.call_count == 1


async def test_options_reload(hass, entry, mock_dhl):
    await setup(hass, entry)
    old = entry.runtime_data
    hass.config_entries.async_update_entry(entry, options={"max_age_minutes": 120})
    await hass.async_block_till_done()
    assert entry.runtime_data is not old
    assert entry.runtime_data.max_age == timedelta(minutes=120)
    assert old._cancel_expiry is None


async def test_multiple_stations_are_independent(hass, entry, mock_dhl, station):
    await setup(hass, entry)
    other = deepcopy(station)
    other.update(primaryKeyPF="1-33104182", zipCode="33104", primaryKeyZipRegion="182")
    other["liveStatus"]["freeCompartmentsS"] = 0
    mock_dhl.get(f"{API_BASE}/locationByPrimaryKeyPF/1-33104182", json=other)
    other_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Other",
        unique_id="1-33104182",
        data={
            "postal_code": "33104",
            "station_number": "182",
            "primary_key": "1-33104182",
        },
    )
    other_entry.add_to_hass(hass)
    await setup(hass, other_entry)
    assert len(er.async_get(hass).entities) == 12
    assert hass.states.get(entity_id(hass, "free_s")).state == "9"
    assert hass.states.get(entity_id(hass, "free_s", station="1-33104182")).state == "0"
