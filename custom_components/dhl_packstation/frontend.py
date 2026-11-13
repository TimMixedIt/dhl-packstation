"""Serve and load bundled cards without modifying the user's dashboards."""

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

STATIC_URL = "/dhl_packstation"


async def async_setup_cards(hass: HomeAssistant) -> None:
    """Register public code only; station data stays in authenticated HA states."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, str(Path(__file__).parent / "www"), False)]
    )
    integration = await async_get_integration(hass, DOMAIN)
    add_extra_js_url(hass, f"{STATIC_URL}/cards.js?v={integration.version}")
