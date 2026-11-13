"""DHL Packstation availability integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import PackstationClient
from .const import DOMAIN
from .coordinator import PackstationConfigEntry, PackstationCoordinator
from .frontend import async_setup_cards

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Load bundled cards when the Home Assistant frontend is enabled."""
    if "frontend" in hass.config.components:
        await async_setup_cards(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: PackstationConfigEntry) -> bool:
    """Set up a validated station, retrying transient failures later."""
    coordinator = PackstationCoordinator(
        hass, entry, PackstationClient(async_get_clientsession(hass))
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(coordinator.async_cancel_expiry)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_reload_entry(
    hass: HomeAssistant, entry: PackstationConfigEntry
) -> None:
    """Apply changed freshness settings."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: PackstationConfigEntry
) -> bool:
    """Unload all station entities."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
