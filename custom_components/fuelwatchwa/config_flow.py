"""Config flow for the FuelWatch WA integration."""
from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import voluptuous as vol

from .const import (
    COMMON_SUBURBS,
    CONF_FUEL_TYPES,
    CONF_LOCATION,
    CONF_SURROUNDING,
    DEFAULT_SURROUNDING,
    DOMAIN,
    FUEL_TYPE_NAMES,
    FUEL_TYPE_OPTIONS,
)


class FuelWatchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> FuelWatchOptionsFlow:
        return FuelWatchOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            location = user_input[CONF_LOCATION]
            fuel_types = user_input[CONF_FUEL_TYPES]

            if not location:
                errors[CONF_LOCATION] = "required"
            elif not fuel_types:
                errors[CONF_FUEL_TYPES] = "required"
            else:
                await self.async_set_unique_id(location.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"FuelWatch WA ({location})",
                    data={
                        CONF_LOCATION: location,
                        CONF_FUEL_TYPES: fuel_types,
                        CONF_SURROUNDING: user_input.get(
                            CONF_SURROUNDING, DEFAULT_SURROUNDING
                        ),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_LOCATION): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=COMMON_SUBURBS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    ),
                ),
                vol.Required(CONF_FUEL_TYPES, default=["diesel"]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=k, label=v)
                            for k, v in FUEL_TYPE_NAMES.items()
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    ),
                ),
                vol.Required(
                    CONF_SURROUNDING, default=DEFAULT_SURROUNDING
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class FuelWatchOptionsFlow(config_entries.OptionsFlow):
    """Handle options for an existing FuelWatch WA entry."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SURROUNDING,
            self.config_entry.data.get(CONF_SURROUNDING, DEFAULT_SURROUNDING),
        )
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SURROUNDING, default=current
                ): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
