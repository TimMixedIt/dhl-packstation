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
    TextSelector,
)

from .api import (
    InvalidResponse,
    PackstationClient,
    PackstationError,
    StationNotFound,
    normalize_location,
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

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate the exact location with DHL before creating an entry."""
        errors = {}
        if user_input is not None:
            try:
                postal_code, station_number = normalize_location(
                    user_input[CONF_POSTAL_CODE], user_input[CONF_STATION_NUMBER]
                )
            except ValueError:
                errors["base"] = "invalid_location"
            else:
                client = PackstationClient(async_get_clientsession(self.hass))
                try:
                    station = await client.async_resolve(postal_code, station_number)
                except StationNotFound:
                    errors["base"] = "station_not_found"
                except InvalidResponse:
                    errors["base"] = "invalid_response"
                except PackstationError:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(station.primary_key)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"Packstation {station_number} · {postal_code} {station.city}",
                        data={
                            CONF_POSTAL_CODE: postal_code,
                            CONF_STATION_NUMBER: station_number,
                            CONF_PRIMARY_KEY: station.primary_key,
                        },
                    )
        return self.async_show_form(
            step_id="user",
            data_schema=probatio.Schema(
                {
                    probatio.Required(CONF_POSTAL_CODE): TextSelector(),
                    probatio.Required(CONF_STATION_NUMBER): TextSelector(),
                }
            ),
            errors=errors,
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
