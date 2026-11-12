"""Test setup and options through Home Assistant's actual flow manager."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.dhl_packstation.const import DOMAIN

from .conftest import LOOKUP_URL

INPUT = {"postal_code": "67141", "station_number": "189"}


async def test_user_flow(hass, mock_dhl):
    with patch(
        "custom_components.dhl_packstation.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], INPUT
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {**INPUT, "primary_key": "1-67141189"}
    assert result["result"].unique_id == "1-67141189"
    assert "Neuhofen" in result["title"]


async def test_duplicate(hass, entry, mock_dhl):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    "status,error",
    [(204, "station_not_found"), (500, "cannot_connect"), (429, "cannot_connect")],
)
async def test_error_can_retry(hass, aioclient_mock, station, status, error):
    aioclient_mock.get(LOOKUP_URL, status=status)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}
    aioclient_mock.clear_requests()
    from .conftest import DETAIL_URL

    aioclient_mock.get(LOOKUP_URL, json={"pfLocations": [station]})
    aioclient_mock.get(DETAIL_URL, json=station)
    with patch(
        "custom_components.dhl_packstation.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], INPUT
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_invalid_response(hass, aioclient_mock):
    aioclient_mock.get(LOOKUP_URL, text="<html>no JSON</html>")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=INPUT
    )
    assert result["errors"] == {"base": "invalid_response"}


async def test_bad_input(hass, aioclient_mock):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={"postal_code": "abc", "station_number": "189"},
    )
    assert result["errors"] == {"base": "invalid_location"}
    assert aioclient_mock.call_count == 0


async def test_options(hass, entry):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"max_age_minutes": 120}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {"max_age_minutes": 120}
