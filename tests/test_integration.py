import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pymodbus.pdu import ExceptionResponse
from pytest_homeassistant.common import MockConfigEntry

from custom_components.flaktgroup.const import DOMAIN, HoldingRegisters


async def setup(hass, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_flow_duplicate_legacy_host(hass, entry, client):
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert form["errors"] == {}
    result = await hass.config_entries.flow.async_configure(
        form["flow_id"], {**entry.data, "host": "RDKS", "name": "Duplicate"}
    )
    assert result["reason"] == "already_configured"
    client.read_holding_registers.assert_not_awaited()


async def test_flow_checks_protocol(hass, client):
    client.read_holding_registers.return_value = None
    client.read_holding_registers.side_effect = None
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {"host": "rdks", "name": "Ventilation", "port": 8899, "update_interval": 15},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    client.close.assert_called_once()


async def test_first_poll_failure(hass, entry, client):
    client.connected = False
    client.connect.return_value = False
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    client.close.assert_called_once()


async def test_registry_migration_and_two_entries(hass, entry, client):
    registry = er.async_get(hass)
    old = registry.async_get_or_create(
        "sensor", DOMAIN, "2-26", config_entry=entry, suggested_object_id="old_outdoor"
    )
    await setup(hass, entry)
    assert registry.async_get(old.entity_id).unique_id == f"{entry.entry_id}-2-26"
    assert float(hass.states.get(old.entity_id).state) == -1

    second = MockConfigEntry(
        domain=DOMAIN, title=entry.title, data={**entry.data, "host": "other"}
    )
    second.add_to_hass(hass)
    await setup(hass, second)
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{second.entry_id}-2-26")
    assert await hass.config_entries.async_unload(second.entry_id)
    client.close.assert_called_once()


async def test_climate_service_and_write_rejection(hass, entry, client):
    await setup(hass, entry)
    entity_id = er.async_get(hass).async_get_entity_id(
        "climate", DOMAIN, f"{entry.entry_id}-Ventilation_climate"
    )
    assert hass.states.get(entity_id).attributes["preset_mode"] == "2"
    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {"entity_id": entity_id, "preset_mode": "3"},
        blocking=True,
    )
    client.write_register.assert_awaited_once_with(213, 3, device_id=2)
    assert hass.states.get(entity_id).attributes["preset_mode"] == "3"

    client.write_register.side_effect = None
    client.write_register.return_value = ExceptionResponse(6, 2)
    with pytest.raises(HomeAssistantError, match="Could not write register"):
        await hass.services.async_call(
            "climate",
            "set_preset_mode",
            {"entity_id": entity_id, "preset_mode": "1"},
            blocking=True,
        )
    assert hass.states.get(entity_id).attributes["preset_mode"] == "3"


async def test_optional_register_and_recovery(hass, entry, client):
    await setup(hass, entry)
    coordinator = entry.runtime_data.coordinator
    original = client.read_holding_registers.side_effect
    client.read_holding_registers.side_effect = lambda address, **kwargs: (
        ExceptionResponse(3, 2) if address == 26 else original(address, **kwargs)
    )
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert HoldingRegisters.OUTDOOR_AIR_TEMPERATURE.value not in coordinator.data

    client.read_holding_registers.side_effect = TimeoutError()
    await coordinator.async_refresh()
    assert not coordinator.last_update_success

    client.connected = False
    client.read_holding_registers.side_effect = original
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    client.connect.assert_awaited_once()


async def test_settings_validate_and_reread_after_partial_write(hass, entry, client):
    await setup(hass, entry)
    registers = {49: 203, 54: 180, 55: 250}
    original = client.read_holding_registers.side_effect
    from pymodbus.pdu.register_message import (
        ReadHoldingRegistersResponse,
        WriteSingleRegisterResponse,
    )

    client.read_holding_registers.side_effect = lambda address, **kwargs: (
        ReadHoldingRegistersResponse(registers=[registers[address]])
        if address in registers
        else original(address, **kwargs)
    )

    def write(address, value, **kwargs):
        if address == 54:
            return ExceptionResponse(6, 3)
        registers[address] = value
        return WriteSingleRegisterResponse(address=address, registers=[value])

    client.write_register.side_effect = write
    menu = await hass.config_entries.options.async_init(entry.entry_id)
    form = await hass.config_entries.options.async_configure(
        menu["flow_id"], {"next_step_id": "temperature"}
    )
    assert form["step_id"] == "temperature"
    result = await hass.config_entries.options.async_configure(
        menu["flow_id"],
        {
            "temperature_set_point": 20.3,
            "min_supply_temperature": 27,
            "max_supply_temperature": 26,
        },
    )
    assert result["errors"] == {"min_supply_temperature": "invalid_temperature_limits"}
    client.write_register.assert_not_awaited()
    result = await hass.config_entries.options.async_configure(
        menu["flow_id"],
        {
            "temperature_set_point": 20.3,
            "min_supply_temperature": 26,
            "max_supply_temperature": 27,
        },
    )
    assert result["errors"] == {"min_supply_temperature": "error_register_write"}
    assert [call.args for call in client.write_register.await_args_list] == [
        (55, 270),
        (54, 260),
    ]
    assert registers == {49: 203, 54: 180, 55: 270}
    suggested = {
        key.schema: key.description["suggested_value"]
        for key in result["data_schema"].schema
    }
    assert suggested["min_supply_temperature"] == 18
    assert suggested["max_supply_temperature"] == 27


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_reload_and_zero_coil(hass, entry, client):
    await setup(hass, entry)
    entity_id = er.async_get(hass).async_get_entity_id(
        "binary_sensor", DOMAIN, f"{entry.entry_id}-2-94"
    )
    assert hass.states.get(entity_id).state == "off"
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    client.close.assert_called_once()
    assert hass.states.get(entity_id).state == "off"


async def test_flow_creates_entry_for_responding_unit(hass, client):
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {
            "host": " rdks ",
            "name": " Ventilation ",
            "port": 8899,
            "update_interval": 15,
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["host"] == "rdks"
    assert result["title"] == "Ventilation"
    assert client.read_holding_registers.await_args_list[0].kwargs == {
        "count": 1,
        "device_id": 2,
    }
    await hass.async_block_till_done()


async def test_forms_serialize_for_frontend(hass, entry, client):
    import probatio
    from homeassistant.helpers.config_validation import custom_serializer

    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert probatio.to_field_list(
        form["data_schema"], custom_serializer=custom_serializer
    )
    await setup(hass, entry)
    menu = await hass.config_entries.options.async_init(entry.entry_id)
    form = await hass.config_entries.options.async_configure(
        menu["flow_id"], {"next_step_id": "temperature"}
    )
    assert probatio.to_field_list(
        form["data_schema"], custom_serializer=custom_serializer
    )
    result = await hass.config_entries.options.async_configure(
        menu["flow_id"],
        {
            "temperature_set_point": 20.25,
            "min_supply_temperature": 18,
            "max_supply_temperature": 22,
        },
    )
    assert result["errors"] == {"temperature_set_point": "invalid_precision"}
    client.write_register.assert_not_awaited()
