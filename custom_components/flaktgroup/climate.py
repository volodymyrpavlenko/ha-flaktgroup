"""Support for Modbus Register sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FlaktgroupConfigEntry, FlaktgroupModbusDataUpdateCoordinator
from .const import (
    FanModes,
    HoldingRegisters,
    Presets,
)
from .modbus_coordinator import ModbusDatapointContext

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: FlaktgroupConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fläktgroup from a config entry."""
    hass_config = config_entry.runtime_data
    device_info = hass_config.device_info
    entities = [
        FlaktgroupClimate(
            hass_config.coordinator,
            device_info,
        ),
    ]
    async_add_entities(entities)


class FlaktgroupClimate(CoordinatorEntity, ClimateEntity):
    """Flaktgroup Climate."""

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.PRESET_MODE
    )

    def __init__(
        self,
        coordinator: FlaktgroupModbusDataUpdateCoordinator,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the Flaktgroup Climate."""
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}-{device_info.get('name')}_climate"
        )
        self._attr_device_info = device_info
        self.entity_description = ClimateEntityDescription(
            key="climate_entity", translation_key="climate_entity", has_entity_name=True
        )

        self._attr_native_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_min_temp = 7
        self._attr_max_temp = 35
        self._attr_native_target_temperature_step = 0.5

        self._attr_fan_modes: list[str] = [str(fan_mode.value) for fan_mode in FanModes]
        self._attr_hvac_modes = [HVACMode.AUTO, HVACMode.OFF]
        self._attr_hvac_mode = HVACMode.AUTO
        self._attr_preset_modes: list[str] = [str(preset.value) for preset in Presets]
        self._attr_preset_mode = None
        super().__init__(
            coordinator,
            ModbusDatapointContext(
                {
                    HoldingRegisters.FAN_MODE.value,
                    HoldingRegisters.PRESET_MODE.value,
                    HoldingRegisters.HUMIDITY_1.value,
                    HoldingRegisters.SUPPLY_AIR_TEMPERATURE.value,
                    HoldingRegisters.TEMPERATURE_SET_POINT.value,
                },
                lambda: self.enabled,
            ),
        )

    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data
        target = data.get(HoldingRegisters.TEMPERATURE_SET_POINT.value)
        supply = data.get(HoldingRegisters.SUPPLY_AIR_TEMPERATURE.value)
        speed = data.get(HoldingRegisters.FAN_MODE.value)
        preset = data.get(HoldingRegisters.PRESET_MODE.value)
        self._attr_native_target_temperature = (
            round(target * 0.1, 1) if target is not None else None
        )
        self._attr_native_current_temperature = (
            round(supply * 0.1, 1) if supply is not None else None
        )
        self._attr_current_humidity = data.get(HoldingRegisters.HUMIDITY_1.value)
        self._attr_fan_mode = (
            str(speed) if speed in FanModes._value2member_map_ else None
        )
        self._attr_preset_mode = (
            str(preset) if preset in Presets._value2member_map_ else None
        )
        self._attr_hvac_mode = HVACMode.OFF if preset == Presets.STOP else HVACMode.AUTO
        super()._handle_coordinator_update()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new target preset mode."""
        if preset_mode not in self._attr_preset_modes:
            raise ServiceValidationError("Unsupported ventilation preset")
        await self.coordinator.write(
            HoldingRegisters.PRESET_MODE.value, int(preset_mode)
        )
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        if fan_mode not in self.fan_modes:
            raise ServiceValidationError("Fan speed is only adjustable in manual mode")
        await self.coordinator.write(HoldingRegisters.FAN_MODE.value, int(fan_mode))
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Switch between stopped and automatic ventilation."""
        if hvac_mode not in self._attr_hvac_modes:
            raise ServiceValidationError("Unsupported HVAC mode")
        await self.async_set_preset_mode(
            str(Presets.STOP if hvac_mode == HVACMode.OFF else Presets.AUTO)
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = float(kwargs[ATTR_TEMPERATURE])
        if not self.min_temp <= temperature <= self.max_temp:
            raise ServiceValidationError("Temperature is outside the supported range")
        async with self.coordinator.settings_lock:
            await self.coordinator.write(
                HoldingRegisters.TEMPERATURE_SET_POINT.value, round(temperature * 10)
            )
        await self.coordinator.async_request_refresh()

    @property
    def fan_mode(self) -> str | None:
        """Get current fan mode."""
        if self.preset_mode == str(Presets.MANUAL):
            return super().fan_mode
        return None

    @property
    def fan_modes(self) -> list[str] | None:
        """Get available fan modes."""
        if self.preset_mode == str(Presets.MANUAL):
            return super().fan_modes
        return []
