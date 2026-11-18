"""Modbus Data Update Coordinator."""

import logging
import math
from asyncio import Lock
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.client.mixin import ModbusClientMixin
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse

_LOGGER = logging.getLogger(__name__)


class ModbusDatapointType(Enum):
    """Modbus Datapoint Type."""

    HOLDING_REGISTER = 1
    COIL = 2


@dataclass(frozen=True)
class ModbusDatapoint:
    """Modbus datapoint."""

    device_id: int
    type: ModbusDatapointType
    address: int
    scale: float = 1


@dataclass(frozen=True)
class ModbusDatapointContext:
    """Modbus Datapoint Context."""

    modbus_datapoint: ModbusDatapoint | set[ModbusDatapoint]
    enabled: Callable[[], bool]


@dataclass(frozen=True)
class ModbusDatapointDescriptionMixin:
    """SensorEntityDescription for Modbus-backed entities."""

    modbus_datapoint: ModbusDatapoint | None = None
    scale: float | int | None = None

    def from_modbus_value(self, number):
        """Apply scaling if needed."""
        scale = self.scale or 1
        actual_number = number * scale
        if scale < 1:
            decimals = -round(math.log10(scale))
            return round(actual_number, decimals)
        return round(actual_number)


class FlaktgroupModbusDataUpdateCoordinator(DataUpdateCoordinator):
    """Poll one ventilation unit and serialize operations on its Modbus client."""

    def __init__(self, hass, entry) -> None:
        from .const import CONF_UPDATE_INTERVAL

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=timedelta(seconds=entry.data[CONF_UPDATE_INTERVAL]),
        )
        self._client = AsyncModbusTcpClient(
            entry.data["host"], port=entry.data["port"], timeout=3, retries=0
        )
        self._lock = Lock()
        self.settings_lock = Lock()
        self._closed = False

    async def _async_update_data(self) -> dict[ModbusDatapoint, int | bool]:
        from .const import HoldingRegisters

        required = HoldingRegisters.PRESET_MODE.value
        datapoints = {required}
        for context in self.async_contexts():
            if context.enabled():
                points = context.modbus_datapoint
                datapoints.update(points if isinstance(points, Iterable) else (points,))
        try:
            async with self._lock:
                await self._ensure_connected()
                data = {required: await read_point(self._client, required)}
                for point in datapoints - {required}:
                    try:
                        data[point] = await read_point(self._client, point)
                    except UnsupportedRegister:
                        continue
                return data
        except (ModbusException, OSError, TimeoutError) as err:
            raise UpdateFailed(str(err)) from err

    async def read_datapoint(self, point: ModbusDatapoint) -> int | bool:
        async with self._lock:
            try:
                await self._ensure_connected()
                return await read_point(self._client, point)
            except (ModbusException, OSError, TimeoutError) as err:
                raise HomeAssistantError(
                    f"Could not read register {point.address}"
                ) from err

    async def write(self, point: ModbusDatapoint, value: int) -> None:
        """Write a holding register and surface a failed acknowledgement."""
        async with self._lock:
            try:
                await self._ensure_connected()
                response = await self._client.write_register(
                    point.address, value, device_id=point.device_id
                )
                check_response(response)
                if response.address != point.address or response.registers != [value]:
                    raise ModbusException("Unexpected write acknowledgement")
            except (ModbusException, OSError, TimeoutError) as err:
                raise HomeAssistantError(
                    f"Could not write register {point.address}"
                ) from err

    async def _ensure_connected(self) -> None:
        if self._closed:
            raise ModbusException("The Modbus client has been shut down")
        await ensure_connected(self._client)

    async def async_shutdown(self) -> None:
        await super().async_shutdown()
        async with self._lock:
            self._closed = True
            self._client.close()


class UnsupportedRegister(ModbusException):
    """The device does not implement the requested register or coil."""


async def ensure_connected(client: AsyncModbusTcpClient) -> None:
    if not client.connected and not await client.connect():
        raise ModbusException("Could not connect to the Modbus device")


def check_response(response) -> None:
    if isinstance(response, ExceptionResponse) and response.exception_code in (1, 2):
        raise UnsupportedRegister(str(response))
    if response is None or response.isError():
        raise ModbusException(f"Invalid Modbus response: {response}")


async def read_point(
    client: AsyncModbusTcpClient, point: ModbusDatapoint
) -> int | bool:
    if point.type == ModbusDatapointType.COIL:
        response = await client.read_coils(
            point.address, count=1, device_id=point.device_id
        )
        check_response(response)
        if not response.bits:
            raise ModbusException("Empty coil response")
        return bool(response.bits[0])
    response = await client.read_holding_registers(
        point.address, count=1, device_id=point.device_id
    )
    check_response(response)
    if len(response.registers) != 1:
        raise ModbusException("Unexpected holding register count")
    return ModbusClientMixin.convert_from_registers(
        response.registers, ModbusClientMixin.DATATYPE.INT16
    )
