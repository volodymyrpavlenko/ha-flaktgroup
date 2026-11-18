"""Support for Modbus Register sensors."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import FlaktgroupConfigEntry
from .const import HoldingRegisters
from .modbus_coordinator import (
    FlaktgroupModbusDataUpdateCoordinator,
    ModbusDatapointContext,
    ModbusDatapointDescriptionMixin,
)

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class ModbusDatapointSensorDescription(
    ModbusDatapointDescriptionMixin, SensorEntityDescription
):
    """Modbus Datapoint Sensor Description."""


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: FlaktgroupConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fläktgroup sensors from a config entry."""
    hass_config = config_entry.runtime_data

    entities = [
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _temperature_sensor_description(
                "supply_air_temperature", HoldingRegisters.SUPPLY_AIR_TEMPERATURE
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _temperature_sensor_description(
                "outdoor_air_temperature", HoldingRegisters.OUTDOOR_AIR_TEMPERATURE
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _temperature_sensor_description(
                "extract_air_temperature", HoldingRegisters.EXTRACT_AIR_TEMPERATURE
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _temperature_sensor_description(
                "freezing_protection_post_heater",
                HoldingRegisters.FREEZING_PROTECTION_POST_HEATER,
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_enabled_default=False,
                icon="mdi:heating-coil",
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _temperature_sensor_description(
                "defrost_air",
                HoldingRegisters.DEFROST_AIR,
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _sensor_description(
                "CO2",
                HoldingRegisters.CO2,
                SensorDeviceClass.CO2,
                "ppm",
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _sensor_description(
                "humidity_1",
                HoldingRegisters.HUMIDITY_1,
                SensorDeviceClass.HUMIDITY,
                "%",
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _sensor_description(
                "humidity_2",
                HoldingRegisters.HUMIDITY_2,
                SensorDeviceClass.HUMIDITY,
                "%",
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _sensor_description(
                "pressure_supply_air",
                HoldingRegisters.PRESSURE_SUPPLY_AIR,
                SensorDeviceClass.ATMOSPHERIC_PRESSURE,
                "%",
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _sensor_description(
                "pressure_extract_air",
                HoldingRegisters.PRESSURE_EXTRACT_AIR,
                SensorDeviceClass.ATMOSPHERIC_PRESSURE,
                "%",
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _sensor_description(
                "airflow_supply_air",
                HoldingRegisters.AIRFLOW_SUPPLY_AIR,
                SensorDeviceClass.WIND_SPEED,
                "l/s",
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _sensor_description(
                "airflow_extract_air",
                HoldingRegisters.AIRFLOW_EXTRACT_AIR,
                SensorDeviceClass.WIND_SPEED,
                "l/s",
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _sensor_description(
                "fan_speed_supply_air",
                HoldingRegisters.FAN_SPEED_SUPPLY_AIR,
                None,
                "%",
                icon="mdi:fan",
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _sensor_description(
                "fan_speed_extract_air",
                HoldingRegisters.FAN_SPEED_EXTRACT_AIR,
                None,
                "%",
                icon="mdi:fan",
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _sensor_description(
                "post_heating",
                HoldingRegisters.POST_HEATING,
                None,
                "%",
                entity_registry_enabled_default=False,
                icon="mdi:heating-coil",
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _sensor_description(
                "pre_heating",
                HoldingRegisters.PRE_HEATING,
                None,
                "%",
                entity_registry_enabled_default=False,
                icon="mdi:heating-coil",
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _sensor_description(
                "cooling",
                HoldingRegisters.COOLING,
                None,
                "%",
                entity_registry_enabled_default=False,
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _sensor_description(
                "rotary_heat_exchanger",
                HoldingRegisters.ROTARY_HEAT_EXCHANGER,
                None,
                "%",
            ),
        ),
        FlaktgroupSensor(
            hass_config.coordinator,
            hass_config.device_info,
            _temperature_sensor_description(
                "active_temperature_setpoint",
                HoldingRegisters.ACTIVE_TEMPERATURE_SETPOINT,
            ),
        ),
    ]
    async_add_entities(entities)


def _temperature_sensor_description(
    kk,
    holding_register_address: HoldingRegisters,
    entity_category=None,
    entity_registry_enabled_default=True,
    icon=None,
):
    return _sensor_description(
        kk,
        holding_register_address,
        SensorDeviceClass.TEMPERATURE,
        "°C",
        entity_category,
        entity_registry_enabled_default,
        icon,
        0.1,
    )


def _sensor_description(
    kk,
    holding_register: HoldingRegisters,
    device_class,
    native_unit_of_measurement,
    entity_category=None,
    entity_registry_enabled_default=True,
    icon=None,
    scale: float = 1,
):
    opt = {}
    if entity_category:
        opt["entity_category"] = entity_category
    if icon:
        opt["icon"] = icon
    key = slugify(holding_register.name)
    return ModbusDatapointSensorDescription(
        key=key,
        translation_key=key,
        has_entity_name=True,
        native_unit_of_measurement=native_unit_of_measurement,
        device_class=device_class,
        modbus_datapoint=holding_register.value,
        scale=scale,
        entity_registry_enabled_default=entity_registry_enabled_default,
        **opt,
    )


class FlaktgroupSensor(CoordinatorEntity, SensorEntity):
    """Fläktgroup Sensor."""

    def __init__(
        self,
        coordinator: FlaktgroupModbusDataUpdateCoordinator,
        device_info: DeviceInfo,
        description: ModbusDatapointSensorDescription,
    ) -> None:
        """Initialize the Fläktgroup Sensor."""
        assert description.modbus_datapoint is not None
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}-{description.modbus_datapoint.device_id}-{description.modbus_datapoint.address}"
        self._attr_device_info = device_info
        self.entity_description: ModbusDatapointSensorDescription = description

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
    def native_value(self):
        value = self.coordinator.data.get(self.entity_description.modbus_datapoint)
        return (
            self.entity_description.from_modbus_value(value)
            if value is not None
            else None
        )
