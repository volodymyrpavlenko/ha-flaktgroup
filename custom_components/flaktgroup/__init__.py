"""Support for FläktGroup ventilation units."""

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .modbus_coordinator import FlaktgroupModbusDataUpdateCoordinator

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR, Platform.BINARY_SENSOR]


@dataclass
class RuntimeData:
    """Resources owned by a loaded FläktGroup entry."""

    coordinator: FlaktgroupModbusDataUpdateCoordinator
    device_info: DeviceInfo


type FlaktgroupConfigEntry = ConfigEntry[RuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: FlaktgroupConfigEntry) -> bool:
    """Connect, confirm the unit responds, and forward entity platforms."""
    coordinator = FlaktgroupModbusDataUpdateCoordinator(hass, entry)
    name = entry.data[CONF_NAME]
    device_id = f"{DOMAIN}.{name}-{entry.data[CONF_HOST]}-{entry.data[CONF_PORT]}"
    entry.runtime_data = RuntimeData(
        coordinator,
        DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=name,
            manufacturer="FläktGroup",
            model="RDKS",
        ),
    )
    await coordinator.async_config_entry_first_refresh()
    _migrate_entity_ids(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await coordinator.async_refresh()
    return True


def _migrate_entity_ids(hass: HomeAssistant, entry: FlaktgroupConfigEntry) -> None:
    registry = er.async_get(hass)
    prefix = f"{entry.entry_id}-"
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.platform == DOMAIN and not entity.unique_id.startswith(prefix):
            registry.async_update_entity(
                entity.entity_id, new_unique_id=f"{prefix}{entity.unique_id}"
            )


async def async_unload_entry(hass: HomeAssistant, entry: FlaktgroupConfigEntry) -> bool:
    """Unload the platforms before the entry's cleanup callbacks run."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
