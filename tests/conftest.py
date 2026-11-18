from unittest.mock import AsyncMock, Mock

import pytest
from pymodbus.pdu.bit_message import ReadCoilsResponse
from pymodbus.pdu.register_message import (
    ReadHoldingRegistersResponse,
    WriteSingleRegisterResponse,
)
from pytest_homeassistant.common import MockConfigEntry

from custom_components.flaktgroup.const import DOMAIN


@pytest.fixture
def client(monkeypatch):
    registers = {213: 2, 49: 203, 25: 180, 26: 65526, 202: 1}
    client = Mock(connected=True)
    client.connect = AsyncMock(return_value=True)
    client.read_holding_registers = AsyncMock(
        side_effect=lambda address, **kwargs: ReadHoldingRegistersResponse(
            registers=[registers.get(address, 0)]
        )
    )
    client.read_coils = AsyncMock(return_value=ReadCoilsResponse(bits=[False]))

    def write(address, value, **kwargs):
        registers[address] = value
        return WriteSingleRegisterResponse(address=address, registers=[value])

    client.write_register = AsyncMock(side_effect=write)
    for module in ("config_flow", "modbus_coordinator"):
        monkeypatch.setattr(
            f"custom_components.flaktgroup.{module}.AsyncModbusTcpClient",
            Mock(return_value=client),
        )
    return client


@pytest.fixture
def entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Ventilation",
        data={
            "name": "Ventilation",
            "host": "rdks",
            "port": 8899,
            "update_interval": 15,
        },
    )
    entry.add_to_hass(hass)
    return entry
