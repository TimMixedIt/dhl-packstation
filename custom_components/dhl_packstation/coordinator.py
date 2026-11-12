"""Fetch once for all station entities and expire old observations."""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import PackstationClient, PackstationData, PackstationError, RateLimited
from .const import (
    CONF_MAX_AGE,
    CONF_POSTAL_CODE,
    CONF_PRIMARY_KEY,
    CONF_STATION_NUMBER,
    DEFAULT_MAX_AGE,
    DOMAIN,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)
type PackstationConfigEntry = ConfigEntry[PackstationCoordinator]


class PackstationCoordinator(DataUpdateCoordinator[PackstationData]):
    """Coordinate requests, errors, and freshness for a single station."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: PackstationConfigEntry,
        client: PackstationClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self.entry = entry
        self.max_age = timedelta(
            minutes=entry.options.get(CONF_MAX_AGE, DEFAULT_MAX_AGE)
        )
        self._cancel_expiry: Callable[[], None] | None = None

    @property
    def data_is_fresh(self) -> bool:
        """Check the source observation, not the time of our last request."""
        return self.data.is_fresh(dt_util.utcnow(), self.max_age)

    @callback
    def async_cancel_expiry(self) -> None:
        """Remove the expiry callback when replacing it or unloading."""
        if self._cancel_expiry is not None:
            self._cancel_expiry()
            self._cancel_expiry = None

    @callback
    def _expire_data(self, now: datetime) -> None:
        """Update availability at the expiry time without another HTTP request."""
        self._cancel_expiry = None
        self.async_update_listeners()

    async def _async_update_data(self) -> PackstationData:
        """Fetch the station with the identifier verified during setup."""
        try:
            data = await self.client.async_get_station(
                self.entry.data[CONF_PRIMARY_KEY],
                self.entry.data[CONF_POSTAL_CODE],
                self.entry.data[CONF_STATION_NUMBER],
            )
        except RateLimited as err:
            raise UpdateFailed("DHL rate limit", retry_after=err.retry_after) from err
        except PackstationError as err:
            raise UpdateFailed(str(err)) from err
        self.async_cancel_expiry()
        if data.is_fresh(dt_util.utcnow(), self.max_age):
            self._cancel_expiry = async_track_point_in_utc_time(
                self.hass, self._expire_data, data.source_timestamp + self.max_age
            )
        return data
