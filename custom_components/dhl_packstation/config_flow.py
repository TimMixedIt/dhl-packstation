"""Set up Packstations and configure the accepted age of DHL data."""

from typing import Any

import probatio
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
)

from .api import (
    InvalidResponse,
    NearbyStation,
    PackstationClient,
    PackstationData,
    PackstationError,
    StationNotFound,
)
from .const import (
    CONF_MAX_AGE,
    CONF_POSTAL_CODE,
    CONF_PRIMARY_KEY,
    CONF_STATION_NUMBER,
    DEFAULT_MAX_AGE,
    DOMAIN,
)
from .coordinator import PackstationConfigEntry


class PackstationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure one entry per station."""

    VERSION = 1

    _nearby: dict[str, NearbyStation]

    def _client(self) -> PackstationClient:
        return PackstationClient(async_get_clientsession(self.hass))

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Use a station number for exact setup, or search by postal code."""
        errors = {}
        if user_input is not None:
            postal = user_input[CONF_POSTAL_CODE]
            number = user_input.get(CONF_STATION_NUMBER, "").strip()
            try:
                if number:
                    return await self._async_create_station(
                        await self._client().async_resolve(postal, number)
                    )
                self._nearby = await self._client().async_nearby(postal)
                if not self._nearby:
                    raise StationNotFound("No lockers nearby")
                return await self.async_step_nearby()
            except ValueError:
                errors["base"] = "invalid_location"
            except StationNotFound:
                errors["base"] = "station_not_found"
            except InvalidResponse:
                errors["base"] = "invalid_response"
            except PackstationError:
                errors["base"] = "cannot_connect"
        return self.async_show_form(
            step_id="user",
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_POSTAL_CODE): TextSelector(),
                    probatio.Optional(CONF_STATION_NUMBER): TextSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_nearby(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm the selected search result against DHL detail data."""
        errors = {}
        if user_input is not None:
            key = user_input[CONF_PRIMARY_KEY]
            if key not in self._nearby:
                errors["base"] = "station_not_found"
            else:
                selection = self._nearby[key]
                try:
                    return await self._async_create_station(
                        await self._client().async_get_station(
                            key, selection.postal_code, selection.station_number
                        )
                    )
                except StationNotFound:
                    errors["base"] = "station_not_found"
                except InvalidResponse:
                    errors["base"] = "invalid_response"
                except PackstationError:
                    errors["base"] = "cannot_connect"
        return self.async_show_form(
            step_id="nearby",
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_PRIMARY_KEY): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(value=key, label=station.label)
                                for key, station in self._nearby.items()
                            ]
                        )
                    ),
                },
            ),
            errors=errors,
        )

    async def _async_create_station(self, station: PackstationData) -> ConfigFlowResult:
        await self.async_set_unique_id(station.primary_key)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"Packstation {station.station_number} · {station.postal_code} {station.city}",
            data={
                CONF_POSTAL_CODE: station.postal_code,
                CONF_STATION_NUMBER: station.station_number,
                CONF_PRIMARY_KEY: station.primary_key,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: PackstationConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return PackstationOptionsFlow()


class PackstationOptionsFlow(OptionsFlow):
    """Let the user decide how old an observation may be."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure the maximum accepted source age."""
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_MAX_AGE: int(user_input[CONF_MAX_AGE])}
            )
        return self.async_show_form(
            step_id="init",
            data_schema=probatio.Schema(
                {
                    probatio.Required(
                        CONF_MAX_AGE,
                        default=self.config_entry.options.get(
                            CONF_MAX_AGE, DEFAULT_MAX_AGE
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=30,
                            max=1440,
                            step=1,
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="min",
                        )
                    ),
                }
            ),
        )
