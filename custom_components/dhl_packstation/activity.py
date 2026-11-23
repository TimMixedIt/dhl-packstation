"""Persist one package request and compact station history."""

import asyncio
import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

import probatio
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .api import PackstationData, valid_primary_key
from .const import COMPARTMENTS, CONF_PRIMARY_KEY, DOMAIN
from .history import record_sample, weekday_totals

SIGNAL_ALARM_UPDATED = f"{DOMAIN}_alarm_updated"
STATION_TIMEZONE = ZoneInfo("Europe/Berlin")
_LOGGER = logging.getLogger(__name__)


def _count(value: int) -> int:
    if type(value) is not int or not 0 <= value <= 99:
        raise probatio.Invalid("Enter a whole number from 0 to 99")
    return value


def _station_id(value: str) -> str:
    if not valid_primary_key(value):
        raise probatio.Invalid("Invalid station identifier")
    return value


class PackstationActivity:
    """Track observations and notify when all requested sizes fit one station."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store = Store(hass, 1, f"{DOMAIN}.activity", private=True)
        self.history: dict[str, dict[str, dict[str, int]]] = {}
        self.alarm: dict = {}
        self._lock = asyncio.Lock()

    async def async_setup(self) -> None:
        """Restore state and expose card and automation actions."""
        data = await self.store.async_load() or {}
        self.history = data.get("history", {})
        self.alarm = data.get("alarm", {})
        async_register_admin_service(
            self.hass,
            DOMAIN,
            "start_alarm",
            self._async_start,
            schema=probatio.Schema(
                {
                    probatio.Required("stations"): [_station_id],
                    probatio.Optional("notifier", default="none"): str,
                    **{
                        probatio.Optional(size, default=0): _count
                        for size in COMPARTMENTS
                    },
                }
            ),
        )
        async_register_admin_service(self.hass, DOMAIN, "stop_alarm", self._async_stop)

    @callback
    def _snapshot(self) -> dict:
        return {"history": self.history, "alarm": self.alarm}

    @property
    def alarm_state(self) -> dict:
        """Expose the current search to dashboard cards."""
        return {key: value for key, value in self.alarm.items() if key != "notifier"}

    def week(self, station: str) -> list[dict]:
        """Return the seven typical totals for one station."""
        today = dt_util.utcnow().astimezone(STATION_TIMEZONE).date()
        return weekday_totals(self.history.get(station, {}), today)

    async def async_remove_station(self, station: str) -> None:
        """Drop history when the integration entry is removed."""
        async with self._lock:
            self.history.pop(station, None)
            if (
                self.alarm.get("status") == "waiting"
                and station in self.alarm["stations"]
            ):
                self.alarm["stations"] = [
                    item for item in self.alarm["stations"] if item != station
                ]
                if not self.alarm["stations"]:
                    self.alarm = {}
            await self._async_save_alarm()

    async def _async_start(self, call: ServiceCall) -> None:
        sizes = {size: call.data[size] for size in COMPARTMENTS}
        stations = list(dict.fromkeys(call.data["stations"]))
        configured = self.hass.config_entries.async_entries(DOMAIN)
        if not any(sizes.values()) or not stations:
            raise HomeAssistantError("Select at least one station and one package")
        if not set(stations) <= {entry.data[CONF_PRIMARY_KEY] for entry in configured}:
            raise HomeAssistantError("Select configured stations")
        notifier = call.data["notifier"].strip() or "none"
        if notifier != "none" and (
            not notifier.startswith("mobile_app_")
            or not self.hass.services.has_service("notify", notifier)
        ):
            raise HomeAssistantError("Select a Home Assistant mobile app")
        async with self._lock:
            if self.alarm.get("status") == "waiting":
                raise HomeAssistantError("Stop the current package alarm first")
            self.alarm = {
                "status": "waiting",
                "sizes": sizes,
                "stations": stations,
                "notifier": notifier,
            }
            await self._async_save_alarm()
            entries = {entry.data[CONF_PRIMARY_KEY]: entry for entry in configured}
            for station_id in stations:
                coordinator = getattr(entries[station_id], "runtime_data", None)
                if (
                    coordinator is not None
                    and coordinator.last_update_success
                    and coordinator.data is not None
                ):
                    if await self._async_match(coordinator.data, coordinator.max_age):
                        break

    async def _async_stop(self, _call: ServiceCall) -> None:
        async with self._lock:
            self.alarm = {}
            await self._async_save_alarm()

    async def _async_save_alarm(self) -> None:
        await self.store.async_save(self._snapshot())
        async_dispatcher_send(self.hass, SIGNAL_ALARM_UPDATED)

    async def async_observe(self, data: PackstationData, max_age: timedelta) -> None:
        """Record a valid complete sample, then check the pending request."""
        now = dt_util.utcnow()
        if not data.is_fresh(now, max_age):
            return
        async with self._lock:
            if data.total is not None:
                local = data.source_timestamp.astimezone(STATION_TIMEZONE)
                record_sample(
                    self.history.setdefault(data.primary_key, {}),
                    local,
                    data.total,
                    now.astimezone(STATION_TIMEZONE).date(),
                )
                self.store.async_delay_save(self._snapshot, 30)
            await self._async_match(data, max_age)

    async def _async_match(self, data: PackstationData, max_age: timedelta) -> bool:
        if (
            self.alarm.get("status") != "waiting"
            or data.primary_key not in self.alarm["stations"]
            or not data.is_fresh(dt_util.utcnow(), max_age)
            or any(
                need
                and (data.compartments[size] is None or data.compartments[size] < need)
                for size, need in self.alarm["sizes"].items()
            )
        ):
            return False
        request = self.alarm
        self.alarm = {**request, "status": "matched", "match": data.primary_key}
        # Persist the claim before delivery so restart cannot dispatch the same alert twice.
        await self._async_save_alarm()
        packages = " · ".join(
            f"{count}× {size.upper()}"
            for size, count in request["sizes"].items()
            if count
        )
        stamp = data.source_timestamp.astimezone(STATION_TIMEZONE).strftime(
            "%d.%m. %H:%M"
        )
        station = f"Packstation {data.station_number} · {data.postal_code} {data.city}"
        title = (
            "Passende Fächer frei"
            if self.hass.config.language.startswith("de")
            else "Matching compartments available"
        )
        message = f"{station}\n{data.address}\n{packages}\nDHL: {stamp}"
        try:
            await self.hass.services.async_call(
                "persistent_notification"
                if request["notifier"] == "none"
                else "notify",
                "create" if request["notifier"] == "none" else request["notifier"],
                {"title": title, "message": message},
                blocking=True,
            )
        except HomeAssistantError:
            _LOGGER.warning("Could not deliver package alarm for %s", data.primary_key)
            self.alarm = request
            await self._async_save_alarm()
            return False
        return True
