"""Fixtures using the actual Home Assistant test harness."""

import json
from pathlib import Path

import pytest

try:
    from pytest_homeassistant.common import MockConfigEntry
    from pytest_homeassistant.common import (
        async_fire_time_changed as async_fire_time_changed,
    )
except ImportError:
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.common import (
        async_fire_time_changed as async_fire_time_changed,
    )

from custom_components.dhl_packstation.const import API_BASE, DOMAIN

DETAIL_URL = f"{API_BASE}/locationByPrimaryKeyPF/1-67141189"
LOOKUP_URL = f"{API_BASE}/nearbySearch?address=67141:189&maxResults=1"


@pytest.fixture(autouse=True)
def _enable_custom_integrations(enable_custom_integrations):
    """Enable this local custom integration."""


@pytest.fixture(autouse=True)
def _freeze_time(freezer):
    """Make source timestamps and expiry reproducible."""
    freezer.move_to("2026-11-13T00:00:00+00:00")


@pytest.fixture
def station():
    """Use public station data, unrelated to the user's configured location."""
    data = json.loads((Path(__file__).parent / "fixtures/station.json").read_text())
    data["liveStatus"]["sourceTimestamp"] = "2026-11-12T23:58:00+0000"
    return data


@pytest.fixture
def entry(hass):
    """Create an unloaded config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Packstation 189 · 67141 Neuhofen",
        unique_id="1-67141189",
        data={
            "postal_code": "67141",
            "station_number": "189",
            "primary_key": "1-67141189",
        },
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_dhl(aioclient_mock, station):
    """Mock actual HTTP responses, leaving the integration stack intact."""
    aioclient_mock.get(LOOKUP_URL, json={"pfLocations": [station]})
    aioclient_mock.get(DETAIL_URL, json=station)
    return aioclient_mock
