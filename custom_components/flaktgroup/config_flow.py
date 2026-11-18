"""Config flow to configure Flaktgroup devices."""

from math import isfinite
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector
from homeassistant.util import slugify
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    HoldingRegisters,
)
from .modbus_coordinator import ModbusDatapoint, ensure_connected, read_point


def _numeric_selector(min_value, max_value, unit_of_measurement, step: float = 1):
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=min_value,
            max=max_value,
            mode=selector.NumberSelectorMode.BOX,
            step=step,
            unit_of_measurement=unit_of_measurement,
        )
    )


def _matches_step(value: float, step: float) -> bool:
    return isfinite(value) and round(value / step) == round(value / step, 8)


def _temperature_selector(min_value, max_value):
    return _numeric_selector(min_value, max_value, "°C", 0.1)


class FlaktgroupConfigurationValue:
    """Class that represents Configuration value and it's validator."""

    def __init__(
        self, holding_register: HoldingRegisters, validator, scale: float = 1
    ) -> None:
        """Initialize the Fläktgroup Configuration Value."""
        self.name = slugify(holding_register.name)
        self.datapoint: ModbusDatapoint = holding_register.value
        self.validator = validator
        self.scale = scale


FAN_SPEED_OPTIONS = _numeric_selector(30, 100, "%")

SUPPLY_FAN_CONFIG = [
    FlaktgroupConfigurationValue(
        HoldingRegisters.SUPPLY_FAN_CONFIG_LOW, FAN_SPEED_OPTIONS
    ),
    FlaktgroupConfigurationValue(
        HoldingRegisters.SUPPLY_FAN_CONFIG_NORMAL, FAN_SPEED_OPTIONS
    ),
    FlaktgroupConfigurationValue(
        HoldingRegisters.SUPPLY_FAN_CONFIG_HIGH, FAN_SPEED_OPTIONS
    ),
    FlaktgroupConfigurationValue(
        HoldingRegisters.SUPPLY_FAN_CONFIG_COOKER_HOOD, FAN_SPEED_OPTIONS
    ),
    FlaktgroupConfigurationValue(
        HoldingRegisters.SUPPLY_FAN_CONFIG_FIREPLACE, FAN_SPEED_OPTIONS
    ),
]

EXTRACT_FAN_CONFIG = [
    FlaktgroupConfigurationValue(
        HoldingRegisters.EXTRACT_FAN_CONFIG_LOW, FAN_SPEED_OPTIONS
    ),
    FlaktgroupConfigurationValue(
        HoldingRegisters.EXTRACT_FAN_CONFIG_NORMAL, FAN_SPEED_OPTIONS
    ),
    FlaktgroupConfigurationValue(
        HoldingRegisters.EXTRACT_FAN_CONFIG_HIGH, FAN_SPEED_OPTIONS
    ),
    FlaktgroupConfigurationValue(
        HoldingRegisters.EXTRACT_FAN_CONFIG_COOKER_HOOD, FAN_SPEED_OPTIONS
    ),
    FlaktgroupConfigurationValue(
        HoldingRegisters.EXTRACT_FAN_CONFIG_FIREPLACE, FAN_SPEED_OPTIONS
    ),
]

TEMPERATURE_CONFIG = [
    FlaktgroupConfigurationValue(
        HoldingRegisters.TEMPERATURE_SET_POINT, _temperature_selector(7, 35), scale=0.1
    ),
    FlaktgroupConfigurationValue(
        HoldingRegisters.MIN_SUPPLY_TEMPERATURE,
        _temperature_selector(15, 35),
        scale=0.1,
    ),
    FlaktgroupConfigurationValue(
        HoldingRegisters.MAX_SUPPLY_TEMPERATURE,
        _temperature_selector(15, 35),
        scale=0.1,
    ),
]

AIR_QUALITY_CONFIG = [
    FlaktgroupConfigurationValue(
        HoldingRegisters.SET_POINT_CO2, _numeric_selector(0, 2000, "ppm")
    )
]
MISC_CONFIG = [
    FlaktgroupConfigurationValue(
        HoldingRegisters.DIRTY_FILTER_ALARM_TIME, _numeric_selector(0, 600, "days")
    )
]


class FlaktgroupConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Flaktgroup device config flow."""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> config_entries.OptionsFlow:
        return FlaktgroupOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            name = user_input[CONF_NAME].strip()
            if not host or not name:
                errors["base"] = "invalid_input"
            elif not _matches_step(user_input[CONF_UPDATE_INTERVAL], 1):
                errors[CONF_UPDATE_INTERVAL] = "invalid_precision"
            else:
                await self.async_set_unique_id(f"{host.casefold()}:{port}")
                self._abort_if_unique_id_configured()
                for entry in self._async_current_entries():
                    if (
                        entry.data[CONF_HOST].strip().casefold(),
                        entry.data[CONF_PORT],
                    ) == (host.casefold(), port):
                        return self.async_abort(reason="already_configured")

                client = AsyncModbusTcpClient(host, port=port, timeout=3, retries=0)
                try:
                    await ensure_connected(client)
                    await read_point(client, HoldingRegisters.PRESET_MODE.value)
                except ModbusException, OSError, TimeoutError:
                    errors["base"] = "cannot_connect"
                finally:
                    client.close()
                if not errors:
                    return self.async_create_entry(
                        title=name,
                        data={**user_input, CONF_HOST: host, CONF_NAME: name},
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=8899): cv.port,
                vol.Required(CONF_UPDATE_INTERVAL, default=15): _numeric_selector(
                    1, 9999, "s"
                ),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )


class FlaktgroupOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Fläktgroup options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the configuration menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "extract_fan",
                "supply_fan",
                "temperature",
                "air_quality",
                "misc",
            ],
        )

    async def async_step_extract_fan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the flow to configure Exhaust Fan."""
        return await self._async_show_config_form(
            "extract_fan", EXTRACT_FAN_CONFIG, user_input
        )

    async def async_step_supply_fan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the flow to configure Supply Fan."""
        return await self._async_show_config_form(
            "supply_fan", SUPPLY_FAN_CONFIG, user_input
        )

    async def async_step_temperature(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the flow to configure Temperature."""
        return await self._async_show_config_form(
            "temperature", TEMPERATURE_CONFIG, user_input
        )

    async def async_step_air_quality(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the flow to configure Air Quality."""
        return await self._async_show_config_form(
            "air_quality", AIR_QUALITY_CONFIG, user_input
        )

    async def async_step_misc(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the flow to configure Air Quality."""
        return await self._async_show_config_form("misc", MISC_CONFIG, user_input)

    async def _async_show_config_form(
        self,
        form_name: str,
        form_config: list[FlaktgroupConfigurationValue],
        user_input: dict[str, Any] | None,
    ) -> FlowResult:
        errors = {}
        values = {}
        placeholders = {f"{parameter.name}_result": "" for parameter in form_config}

        if self.config_entry.state is not config_entries.ConfigEntryState.LOADED:
            return self.async_abort(reason="not_loaded")
        coordinator = self.config_entry.runtime_data.coordinator
        async with coordinator.settings_lock:
            try:
                for parameter in form_config:
                    raw = await coordinator.read_datapoint(parameter.datapoint)
                    values[parameter.name] = round(raw * parameter.scale, 1)
            except HomeAssistantError:
                return self.async_abort(reason="cannot_read")

            if user_input is not None:
                minimum = "min_supply_temperature"
                maximum = "max_supply_temperature"
                if (
                    form_name == "temperature"
                    and user_input[minimum] > user_input[maximum]
                ):
                    errors[minimum] = "invalid_temperature_limits"
                for parameter in form_config:
                    if not _matches_step(
                        user_input[parameter.name], parameter.validator.config["step"]
                    ):
                        errors[parameter.name] = "invalid_precision"
                if not errors:
                    ordered = form_config
                    if (
                        form_name == "temperature"
                        and user_input[minimum] > values[maximum]
                    ):
                        ordered = [form_config[0], form_config[2], form_config[1]]
                    for parameter in ordered:
                        name = parameter.name
                        if user_input[name] == values[name]:
                            continue
                        try:
                            await coordinator.write(
                                parameter.datapoint,
                                round(user_input[name] / parameter.scale),
                            )
                        except HomeAssistantError:
                            errors[name] = "error_register_write"
                            break
                    for parameter in form_config:
                        try:
                            raw = await coordinator.read_datapoint(parameter.datapoint)
                        except HomeAssistantError:
                            errors["base"] = "cannot_read"
                            values.pop(parameter.name, None)
                        else:
                            values[parameter.name] = round(raw * parameter.scale, 1)
                    await coordinator.async_request_refresh()

        return self.async_show_form(
            step_id=form_name,
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({vol.Required(p.name): p.validator for p in form_config}),
                values,
            ),
            description_placeholders=placeholders,
            errors=errors,
        )
