"""Exercise persistent one-shot alarms and the weekly signal."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import probatio
import pytest
from homeassistant.core import Context
from homeassistant.exceptions import HomeAssistantError, Unauthorized
from homeassistant.setup import async_setup_component

from custom_components.dhl_packstation.activity import PackstationActivity
from custom_components.dhl_packstation.const import DOMAIN
from custom_components.dhl_packstation.history import record_sample, weekday_totals

from .conftest import DETAIL_URL
from .test_integration import entity_id, setup

STATION = "1-67141189"


def test_week_uses_two_dates_and_prunes_old_samples():
    now = datetime.fromisoformat("2026-11-23T11:00:00+01:00")
    today = now.date()
    days = {"2026-09-01": {"11": 99}}
    record_sample(days, now - timedelta(weeks=1), 0, today)
    assert weekday_totals(days, today)[0] == {"days": 1, "typical": None}
    record_sample(days, now, 8, today)
    record_sample(days, now + timedelta(minutes=15), 99, today)
    assert weekday_totals(days, today)[0] == {"days": 2, "typical": 4.0}
    assert weekday_totals(days, today)[6] == {"days": 0, "typical": None}
    assert "2026-09-01" not in days


async def test_waiting_alarm_ignores_stale_matches_and_persists(
    hass, entry, mock_dhl, station
):
    notify = AsyncMock()
    hass.services.async_register("notify", "mobile_app_test", notify)
    station["geoPosition"] = {"latitude": 49.4, "longitude": 8.4}
    station["liveStatus"]["freeCompartmentsM"] = 1
    mock_dhl.clear_requests()
    mock_dhl.get(DETAIL_URL, json=station)
    await setup(hass, entry)
    await hass.services.async_call(
        DOMAIN,
        "start_alarm",
        {
            "stations": [STATION, STATION],
            "s": 1,
            "m": 2,
            "notifier": "mobile_app_test",
        },
        blocking=True,
    )
    notify.assert_not_called()
    total = hass.states.get(entity_id(hass, "free_total"))
    assert total.attributes["latitude"] == 49.4
    assert total.attributes["alarm"]["status"] == "waiting"
    assert "notifier" not in total.attributes["alarm"]

    activity = PackstationActivity(hass)
    await activity.async_setup()
    assert activity.alarm_state["status"] == "waiting"
    station["liveStatus"]["freeCompartmentsM"] = 2
    station["liveStatus"]["sourceTimestamp"] = "2026-11-12T10:00:00Z"
    mock_dhl.clear_requests()
    mock_dhl.get(DETAIL_URL, json=station)
    entry.runtime_data.activity = activity
    await entry.runtime_data.async_refresh()
    notify.assert_not_called()

    station["liveStatus"]["sourceTimestamp"] = "2026-11-12T23:58:00Z"
    mock_dhl.clear_requests()
    mock_dhl.get(DETAIL_URL, json=station)
    await entry.runtime_data.async_refresh()
    await entry.runtime_data.async_refresh()
    notify.assert_awaited_once()
    assert "1× S · 2× M" in notify.call_args.args[0].data["message"]
    restored = PackstationActivity(hass)
    await restored.async_setup()
    await restored.async_observe(entry.runtime_data.data, entry.runtime_data.max_age)
    notify.assert_awaited_once()
    assert restored.alarm_state["match"] == STATION


async def test_alarm_immediate_inbox_and_cancel(hass, entry, mock_dhl):
    await setup(hass, entry)
    assert await async_setup_component(hass, "persistent_notification", {})
    await hass.services.async_call(
        DOMAIN, "start_alarm", {"stations": [STATION], "m": 2}, blocking=True
    )
    assert hass.data[DOMAIN].alarm_state["status"] == "matched"
    await hass.services.async_call(
        DOMAIN, "start_alarm", {"stations": [STATION], "m": 99}, blocking=True
    )
    assert hass.data[DOMAIN].alarm_state["status"] == "waiting"
    with pytest.raises(HomeAssistantError, match="Stop the current"):
        await hass.services.async_call(
            DOMAIN, "start_alarm", {"stations": [STATION], "m": 99}, blocking=True
        )
    await hass.services.async_call(DOMAIN, "stop_alarm", blocking=True)
    assert hass.data[DOMAIN].alarm_state == {}


@pytest.mark.parametrize(
    ("data", "error"),
    [
        ({"stations": [STATION]}, HomeAssistantError),
        ({"stations": [], "m": 1}, HomeAssistantError),
        ({"stations": ["1-27777172"], "m": 1}, HomeAssistantError),
        ({"stations": [STATION], "m": 1, "notifier": "irrelevant"}, HomeAssistantError),
        (
            {"stations": [STATION], "m": 1, "notifier": "mobile_app_missing"},
            HomeAssistantError,
        ),
        ({"stations": [STATION], "m": False}, probatio.Invalid),
        ({"stations": ["../wrong"], "m": 1}, probatio.Invalid),
    ],
)
async def test_reject_invalid_alarm(hass, entry, mock_dhl, data, error):
    await setup(hass, entry)
    with pytest.raises(error):
        await hass.services.async_call(DOMAIN, "start_alarm", data, blocking=True)


async def test_removing_station_clears_pending_alarm_and_history(hass, entry, mock_dhl):
    await setup(hass, entry)
    activity = hass.data[DOMAIN]
    assert STATION in activity.history
    await hass.services.async_call(
        DOMAIN, "start_alarm", {"stations": [STATION], "m": 99}, blocking=True
    )
    await hass.config_entries.async_remove(entry.entry_id)
    assert activity.alarm_state == {}
    assert STATION not in activity.history


async def test_notification_failure_keeps_request(hass, entry, mock_dhl):
    notify = AsyncMock(side_effect=HomeAssistantError("phone unavailable"))
    hass.services.async_register("notify", "mobile_app_test", notify)
    await setup(hass, entry)
    await hass.services.async_call(
        DOMAIN,
        "start_alarm",
        {
            "stations": [STATION],
            "s": 1,
            "notifier": "mobile_app_test",
        },
        blocking=True,
    )
    assert hass.data[DOMAIN].alarm_state["status"] == "waiting"
    notify.side_effect = None
    await entry.runtime_data.async_refresh()
    assert hass.data[DOMAIN].alarm_state["status"] == "matched"


async def test_alarm_requires_admin(hass, entry, mock_dhl, hass_read_only_user):
    await setup(hass, entry)
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            "start_alarm",
            {"stations": [STATION], "s": 1},
            context=Context(user_id=hass_read_only_user.id),
            blocking=True,
        )


async def test_alarm_does_not_combine_stations(hass, entry, mock_dhl, station):
    from dataclasses import replace

    from .conftest import MockConfigEntry

    station["liveStatus"]["freeCompartmentsM"] = 1
    mock_dhl.clear_requests()
    mock_dhl.get(DETAIL_URL, json=station)
    await setup(hass, entry)
    other_id = "13-27777606"
    other = MockConfigEntry(
        domain=DOMAIN,
        unique_id=other_id,
        data={"postal_code": "27777", "station_number": "606", "primary_key": other_id},
    )
    other.add_to_hass(hass)
    notify = AsyncMock()
    hass.services.async_register("notify", "mobile_app_test", notify)
    await hass.services.async_call(
        DOMAIN,
        "start_alarm",
        {
            "stations": [STATION, other_id],
            "s": 1,
            "m": 2,
            "notifier": "mobile_app_test",
        },
        blocking=True,
    )
    coordinator = entry.runtime_data
    sample = replace(
        coordinator.data,
        primary_key=other_id,
        compartments={"s": 0, "m": 2, "l": 0, "xl": 0},
    )
    await coordinator.activity.async_observe(sample, coordinator.max_age)
    notify.assert_not_called()
    ready = replace(sample, compartments={"s": 1, "m": 2, "l": None, "xl": None})
    await coordinator.activity.async_observe(ready, coordinator.max_age)
    notify.assert_awaited_once()
    assert coordinator.activity.alarm_state["match"] == other_id
