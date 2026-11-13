"""Check bundled static assets, automatic loading, and discovery metadata."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.setup import async_setup_component

from custom_components.dhl_packstation import async_setup
from custom_components.dhl_packstation.const import DOMAIN
from custom_components.dhl_packstation.frontend import async_setup_cards

from .test_integration import entity_id, setup


async def test_cards_register_once_per_integration(hass):
    hass.data[DATA_EXTRA_MODULE_URL] = set()
    hass.config.components.add("frontend")
    with patch.object(hass, "http", create=True) as http:
        http.async_register_static_paths = AsyncMock()
        assert await async_setup(hass, {})
        http.async_register_static_paths.assert_awaited_once()
        config = http.async_register_static_paths.call_args.args[0][0]
        assert config.url_path == "/dhl_packstation"
        assert config.cache_headers is False
        for name in ["cards.js", "data.js", "view.js", "styles.js", "editor.js"]:
            assert (Path(config.path) / name).is_file()
    assert hass.data[DATA_EXTRA_MODULE_URL] == {"/dhl_packstation/cards.js?v=0.2.0b2"}


async def test_static_modules_are_served(hass, hass_client):
    assert await async_setup_component(hass, "http", {"http": {}})
    hass.data[DATA_EXTRA_MODULE_URL] = set()
    await async_setup_cards(hass)
    client = await hass_client()
    response = await client.get("/dhl_packstation/cards.js")
    assert response.status == 200
    assert "dhl-packstation-overview-card" in await response.text()
    assert "javascript" in response.content_type
    response = await client.get("/dhl_packstation/../manifest.json")
    assert response.status == 404


async def test_entity_metadata_for_cards(hass, entry, mock_dhl):
    await setup(hass, entry)
    registry = hass.states.get(entity_id(hass, "free_s")).attributes
    assert registry["dhl_packstation_id"] == "1-67141189"
    assert registry["dhl_packstation_key"] == "free_s"
    assert registry["station_number"] == "189"
    assert registry["address"] == "Industriestr. 10"
    assert DOMAIN == "dhl_packstation"
