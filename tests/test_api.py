"""Check DHL identifiers, HTTP failures, and data interpretation."""

from datetime import UTC, datetime, timedelta

import pytest
from aiohttp import ClientConnectionError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.dhl_packstation.api import (
    InvalidResponse,
    PackstationClient,
    PackstationError,
    RateLimited,
    StationNotFound,
    normalize_location,
)

from .conftest import DETAIL_URL, LOOKUP_URL


@pytest.fixture
async def client(hass, aioclient_mock):
    return PackstationClient(async_get_clientsession(hass))


async def test_resolve(client, mock_dhl):
    station = await client.async_resolve(" 67141 ", "0189")
    assert station.primary_key == "1-67141189"
    assert station.compartments == {"s": 9, "m": 10, "l": 8, "xl": 1}
    assert station.address == "Industriestr. 10"
    assert station.source_timestamp == datetime(2026, 11, 12, 23, 58, tzinfo=UTC)
    assert mock_dhl.call_count == 2


@pytest.mark.parametrize(
    "postal,number",
    [
        ("1234", "1"),
        ("ABCDE", "189"),
        ("123456", "189"),
        ("67141", "0"),
        ("67141", "../../a"),
        ("67141", "12345"),
        ("６７１４１", "189"),
        ("67141", "-1"),
    ],
)
async def test_bad_input_makes_no_request(client, aioclient_mock, postal, number):
    with pytest.raises(ValueError):
        await client.async_resolve(postal, number)
    assert aioclient_mock.call_count == 0


def test_leading_zero_postcode():
    assert normalize_location("01067", "001") == ("01067", "1")


@pytest.mark.parametrize(
    "changes",
    [
        {"zipCode": "67142"},
        {"primaryKeyZipRegion": "190"},
        {"locationType": "POSTFILIALE"},
    ],
)
async def test_lookup_does_not_accept_wrong_station(
    client, aioclient_mock, station, changes
):
    station.update(changes)
    aioclient_mock.get(LOOKUP_URL, json={"pfLocations": [station]})
    with pytest.raises(StationNotFound):
        await client.async_resolve("67141", "189")
    assert aioclient_mock.call_count == 1


@pytest.mark.parametrize(
    "response,error",
    [
        ({"pfLocations": []}, StationNotFound),
        ({}, InvalidResponse),
        ({"pfLocations": {}}, InvalidResponse),
        ({"pfLocations": [None]}, InvalidResponse),
    ],
)
async def test_bad_lookup(client, aioclient_mock, response, error):
    aioclient_mock.get(LOOKUP_URL, json=response)
    with pytest.raises(error):
        await client.async_resolve("67141", "189")


@pytest.mark.parametrize("primary_key", ["../bad", 123, None])
async def test_lookup_identifier_validation(
    client, aioclient_mock, station, primary_key
):
    station["primaryKeyPF"] = primary_key
    aioclient_mock.get(LOOKUP_URL, json={"pfLocations": [station]})
    with pytest.raises(InvalidResponse):
        await client.async_resolve("67141", "189")


async def test_direct_identifier_validation(client, aioclient_mock):
    with pytest.raises(InvalidResponse):
        await client.async_get_station("../bad", "67141", "189")
    assert aioclient_mock.call_count == 0


@pytest.mark.parametrize(
    "status,error",
    [
        (204, StationNotFound),
        (404, StationNotFound),
        (403, PackstationError),
        (500, PackstationError),
        (503, PackstationError),
        (302, PackstationError),
    ],
)
async def test_http_errors(client, aioclient_mock, status, error):
    aioclient_mock.get(DETAIL_URL, status=status)
    with pytest.raises(error):
        await client.async_get_station("1-67141189", "67141", "189")


@pytest.mark.parametrize(
    "header,seconds",
    [
        ("3600", 3600),
        ("1", 900),
        ("invalid", 900),
        ("Fri, 13 Nov 2026 01:00:00 GMT", 3600),
        ("172800", 172800),
    ],
)
async def test_rate_limit(client, aioclient_mock, header, seconds):
    aioclient_mock.get(DETAIL_URL, status=429, headers={"Retry-After": header})
    with pytest.raises(RateLimited) as caught:
        await client.async_get_station("1-67141189", "67141", "189")
    assert caught.value.retry_after == seconds


@pytest.mark.parametrize("error", [TimeoutError(), ClientConnectionError()])
async def test_network_errors(client, aioclient_mock, error):
    aioclient_mock.get(DETAIL_URL, exc=error)
    with pytest.raises(PackstationError):
        await client.async_get_station("1-67141189", "67141", "189")


@pytest.mark.parametrize("text", ["<html>error</html>", "[]", "null"])
async def test_not_json_object(client, aioclient_mock, text):
    aioclient_mock.get(DETAIL_URL, text=text)
    with pytest.raises(InvalidResponse):
        await client.async_get_station("1-67141189", "67141", "189")


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, 0),
        (12, 12),
        (None, None),
        (-1, None),
        ("4", None),
        (True, None),
        (1.5, None),
        ({}, None),
    ],
)
async def test_count_validation(client, aioclient_mock, station, value, expected):
    station["liveStatus"]["freeCompartmentsS"] = value
    aioclient_mock.get(DETAIL_URL, json=station)
    data = await client.async_get_station("1-67141189", "67141", "189")
    assert data.compartments["s"] == expected
    assert data.compartments["xl"] == 1


@pytest.mark.parametrize(
    "value",
    [None, "", "broken", "2026-11-12T23:58:00", "0001-01-01T00:00:00+1400", 123],
)
async def test_missing_or_invalid_timestamp(client, aioclient_mock, station, value):
    station["liveStatus"]["sourceTimestamp"] = value
    aioclient_mock.get(DETAIL_URL, json=station)
    data = await client.async_get_station("1-67141189", "67141", "189")
    assert data.source_timestamp is None
    assert not data.is_fresh(datetime.now(UTC), timedelta(hours=1))


@pytest.mark.parametrize(
    "age,fresh",
    [(0, True), (59, True), (60, False), (120, False), (-4, True), (-6, False)],
)
async def test_freshness_boundaries(client, aioclient_mock, station, age, fresh):
    now = datetime(2026, 11, 13, tzinfo=UTC)
    station["liveStatus"]["sourceTimestamp"] = (
        now - timedelta(minutes=age)
    ).isoformat()
    aioclient_mock.get(DETAIL_URL, json=station)
    data = await client.async_get_station("1-67141189", "67141", "189")
    assert data.is_fresh(now, timedelta(hours=1)) is fresh


@pytest.mark.parametrize("live", [None, {}])
async def test_station_without_live_data(client, aioclient_mock, station, live):
    station["liveStatus"] = live
    aioclient_mock.get(DETAIL_URL, json=station)
    data = await client.async_get_station("1-67141189", "67141", "189")
    assert all(value is None for value in data.compartments.values())


async def test_bad_live_shape(client, aioclient_mock, station):
    station["liveStatus"] = []
    aioclient_mock.get(DETAIL_URL, json=station)
    with pytest.raises(InvalidResponse):
        await client.async_get_station("1-67141189", "67141", "189")


async def test_detail_identifier_changed(client, aioclient_mock, station):
    station["primaryKeyPF"] = "1-67141190"
    aioclient_mock.get(DETAIL_URL, json=station)
    with pytest.raises(InvalidResponse):
        await client.async_get_station("1-67141189", "67141", "189")


async def test_optional_metadata(client, aioclient_mock, station):
    for key in ("city", "street", "houseNo", "locationName"):
        station[key] = None
    aioclient_mock.get(DETAIL_URL, json=station)
    data = await client.async_get_station("1-67141189", "67141", "189")
    assert data.address == data.city == data.name == ""
