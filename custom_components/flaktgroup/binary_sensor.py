"""Support for Modbus Register sensors."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import FlaktgroupConfigEntry
from .const import Coils
from .modbus_coordinator import (
    FlaktgroupModbusDataUpdateCoordinator,
    ModbusDatapointContext,
    ModbusDatapointDescriptionMixin,
)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: FlaktgroupConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fläktgroup sensors from a config entry."""
    hass_config = config_entry.runtime_data
    entities = [
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "external_timer_1",
                Coils.EXTERNAL_TIMER_1,
                "mdi:timer-outline",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "external_timer_2",
                Coils.EXTERNAL_TIMER_2,
                "mdi:timer-outline",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "external_timer_2", Coils.COOKER_HOOD_SWITCH, "mdi:stove"
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "summer_winter_mode",
                Coils.SUMMER_WINTER_MODE,
                "mdi:sun-snowflake-variant",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "fire_alarm", Coils.FIRE_ALARM, "mdi:fire-alert"
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "sensor_error_supply_temperature",
                Coils.SENSOR_ERROR_SUPPLY_TEMPERATURE,
                "mdi:thermometer-alert",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "sensor_error_outdoor_temperature",
                Coils.SENSOR_ERROR_OUTDOOR_TEMPERATURE,
                "mdi:thermometer-alert",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "sensor_error_extract_temperature",
                Coils.SENSOR_ERROR_EXTRACT_TEMPERATURE,
                "mdi:thermometer-alert",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "sensor_error_frost_protection",
                Coils.SENSOR_ERROR_FROST_PROTECTION,
                "mdi:snowflake-alert",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "sensor_error_defrost_temperature",
                Coils.SENSOR_ERROR_DEFROST_TEMPERATURE,
                "mdi:snowflake-alert",
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "dirty_filter",
                Coils.DIRTY_FILTER,
                "mdi:filter-check",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "supply_fan_error",
                Coils.SUPPLY_FAN_ERROR,
                "mdi:fan-alert",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "extract_fan_error",
                Coils.EXTRACT_FAN_ERROR,
                "mdi:fan-alert",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "frost_alarm",
                Coils.FROST_ALARM,
                "mdi:snowflake-alert",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "rotary_heat_exchanger_failure",
                Coils.ROTARY_HEAT_EXCHANGER_FAILURE,
                "mdi:fan-alert",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "filter_alarm_supply_air",
                Coils.FILTER_ALARM_SUPPLY_AIR,
                "mdi:filter-check",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "filter_alarm_extract_air",
                Coils.FILTER_ALARM_EXTRACT_AIR,
                "mdi:filter-check",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "overheating_electrical_heater",
                Coils.OVERHEATING_ELECTRICAL_HEATER,
                "mdi:heating-coil",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "pump_heater_malfunction",
                Coils.PUMP_HEATER_MALFUNCTION,
                icon="mdi:alert-circle",
                entity_registry_enabled_default=False,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "freezing_hot_water_battery",
                Coils.FREEZING_HOT_WATER_BATTERY,
                icon="mdi:alert-circle",
                entity_registry_enabled_default=False,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "summary_alarm",
                Coils.SUMMARY_ALARM,
                icon="mdi:alert-circle",
                entity_registry_enabled_default=False,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "pump_cooling_malfunction",
                Coils.PUMP_COOLING_MALFUNCTION,
                icon="mdi:alert-circle",
                entity_registry_enabled_default=False,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "temperature_alarm",
                Coils.TEMPERATURE_ALARM,
                icon="mdi:thermometer-alert",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
        FlaktgroupBinarySensor(
            hass_config.coordinator,
            hass_config.device_info,
            _binary_sensor_description(
                "humidity_control_running",
                Coils.HUMIDITY_CONTROL_RUNNING,
                icon="mdi:water-percent",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ),
    ]
    async_add_entities(entities)


def _binary_sensor_description(
    kk,
    coil: Coils,
    icon=None,
    entity_category=None,
    entity_registry_enabled_default=False,
):
    opt = {}
    if icon:
        opt["icon"] = icon
    key = slugify(coil.name)
    return ModbusDatapointBinarySensorDescription(
        key=key,
        translation_key=key,
        modbus_datapoint=coil.value,
        entity_category=entity_category,
        entity_registry_enabled_default=entity_registry_enabled_default,
        has_entity_name=True,
        **opt,
    )


@dataclass(frozen=True, kw_only=True)
class ModbusDatapointBinarySensorDescription(
    ModbusDatapointDescriptionMixin, BinarySensorEntityDescription
):
    """Modbus Datapoint Binary Sensor Description."""


class FlaktgroupBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Flaktgroup Binary Sensor."""

    def __init__(
        self,
        coordinator: FlaktgroupModbusDataUpdateCoordinator,
        device_info: DeviceInfo,
        description: ModbusDatapointBinarySensorDescription,
    ) -> None:
        """Initialize the Flaktgroup Binary Sensor."""
        assert description.modbus_datapoint is not None
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}-{description.modbus_datapoint.device_id}-{description.modbus_datapoint.address}"
        self._attr_device_info = device_info
        self.entity_description: ModbusDatapointBinarySensorDescription = description

        super().__init__(
            coordinator,
            ModbusDatapointContext(description.modbus_datapoint, lambda: self.enabled),
        )

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.entity_description.modbus_datapoint in self.coordinator.data
        )

    @property
    def is_on(self):
        value = self.coordinator.data.get(self.entity_description.modbus_datapoint)
        return bool(value) if value is not None else None
