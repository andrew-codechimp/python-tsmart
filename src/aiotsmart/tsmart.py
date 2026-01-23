"""Homeassistant Client."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
import socket
import struct
import time
from typing import Any, Self, Callable

from aiotsmart.exceptions import (
    TSmartBadResponseError,
)
from aiotsmart.models import Configuration, Mode, Status
from aiotsmart.util import validate_checksum, add_checksum

from .const import MESSAGE_HEADER, UDP_PORT

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 5  # seconds


# pylint:disable=too-many-locals
def _unpack_configuration_response(
    request: bytearray, data: bytes
) -> Configuration | None:
    """Return unpacked configuration response from TSmart Immersion Heater."""
    response_struct = struct.Struct("=BBBHL32sBBBBB32s28s32s64s124s")

    if len(data) != response_struct.size:
        raise TSmartBadResponseError(
            "Unexpected packet length (got: %d, expected: %d)"
            % (len(data), response_struct.size)
        )

    if data[0] == 0:
        raise TSmartBadResponseError("Got error response (code %d)" % (data[0]))

    if data[0] != request[0]:
        raise TSmartBadResponseError(
            "Unexpected response type (%02X %02X %02X)" % (data[0], data[1], data[2])
        )

    if not validate_checksum(data):
        raise TSmartBadResponseError("Received packet checksum failed")

    # pylint:disable=unused-variable
    (
        cmd,
        sub,
        sub2,
        device_type,
        device_id,
        device_name,
        tz,
        userbin,
        firmware_version_major,
        firmware_version_minor,
        firmware_version_deployment,
        firmware_name,
        legacy,
        wifi_ssid,
        wifi_password,
        unused,
    ) = response_struct.unpack(data)

    configuration = Configuration(
        device_id=f"{device_id:04X}",
        device_name=device_name.decode("utf-8").split("\x00")[0],
        firmware_version=f"{firmware_version_major}.{firmware_version_minor}.{firmware_version_deployment}",
        firmware_name=firmware_name.decode("utf-8").split("\x00")[0],
    )
    _LOGGER.info(
        "Configuration received %s %s"
        % (configuration.device_id, configuration.device_name)
    )

    return configuration


# pylint:disable=too-many-locals
def _unpack_control_read_response(request: bytearray, data: bytes) -> Status | None:
    """Return unpacked control read response from TSmart Immersion Heater."""
    response_struct = struct.Struct("=BBBBHBHBBH16sB")

    if len(data) != response_struct.size:
        raise TSmartBadResponseError(
            "Unexpected packet length (got: %d, expected: %d)"
            % (len(data), response_struct.size)
        )

    if data[0] == 0:
        raise TSmartBadResponseError(("Got error response (code %d)" % (data[0])))

    if data[0] != request[0]:
        raise TSmartBadResponseError(
            "Unexpected response type (%02X %02X %02X)" % (data[0], data[1], data[2])
        )

    if not validate_checksum(data):
        raise TSmartBadResponseError("Received packet checksum failed")

    # pylint:disable=unused-variable
    (
        cmd,
        sub,
        sub2,
        power,
        setpoint,
        mode,
        t_high,
        relay,
        smart_state,
        t_low,
        error_buffer,
        checksum,
    ) = response_struct.unpack(data)

    # Extract 16-bit values (flag in bit 15, counter in bits 0-14)
    e01_value = error_buffer[0] | (error_buffer[1] << 8)
    e02_value = error_buffer[2] | (error_buffer[3] << 8)
    e03_value = error_buffer[4] | (error_buffer[5] << 8)
    e04_value = error_buffer[6] | (error_buffer[7] << 8)
    w01_value = error_buffer[8] | (error_buffer[9] << 8)
    w02_value = error_buffer[10] | (error_buffer[11] << 8)
    w03_value = error_buffer[12] | (error_buffer[13] << 8)
    e05_value = error_buffer[14] | (error_buffer[15] << 8)

    status = Status(
        power=bool(power),
        temperature_average=(t_high + t_low) / 20,
        temperature_high=t_high / 10,
        temperature_low=t_low / 10,
        setpoint=setpoint / 10,
        mode=Mode(mode),
        relay=bool(relay),
        e01=(e01_value >> 15) & 1 == 1,
        e01_count=e01_value & 0x7FFF,
        e02=(e02_value >> 15) & 1 == 1,
        e02_count=e02_value & 0x7FFF,
        e03=(e03_value >> 15) & 1 == 1,
        e03_count=e03_value & 0x7FFF,
        e04=(e04_value >> 15) & 1 == 1,
        e04_count=e04_value & 0x7FFF,
        e05=(e05_value >> 15) & 1 == 1,
        e05_count=e05_value & 0x7FFF,
        w01=(w01_value >> 15) & 1 == 1,
        w01_count=w01_value & 0x7FFF,
        w02=(w02_value >> 15) & 1 == 1,
        w02_count=w02_value & 0x7FFF,
        w03=(w03_value >> 15) & 1 == 1,
        w03_count=w03_value & 0x7FFF,
    )
    return status


# pylint:disable=too-many-locals
def _unpack_control_write_response(_: bytearray, data: bytes) -> None:
    """Return unpacked control write response from TSmart Immersion Heater."""

    if data != b"\xf2\x00\x00\xa7":
        raise TSmartBadResponseError


class TsmartProtocol(asyncio.DatagramProtocol):
    """Protocol to send request and receive responses."""

    def __init__(
        self, request: bytearray, unpack_function: Callable[[bytearray, bytes], Any]
    ) -> None:
        """Initialize with callback function."""
        self.request = request
        self.unpack_function = unpack_function
        self.done = asyncio.get_running_loop().create_future()

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        """Test if responder is a TSmart Immersion Heater."""
        _LOGGER.debug("Received configuration response from %s", addr)
        response = self.unpack_function(self.request, data)

        self.done.set_result(response)


@dataclass
class TSmartClient:
    """TSmart Client."""

    ip_address: str

    def create_socket(self) -> socket.socket:
        """Create a UDP socket."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet, UDP

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", 1337))
        sock.connect((self.ip_address, UDP_PORT))
        return sock

    async def configuration_read(self) -> Configuration:
        """Get configuration from immersion heater."""

        loop = asyncio.get_running_loop()

        sock = self.create_socket()

        request = struct.pack(MESSAGE_HEADER, 0x21, 0, 0, 0)
        request_checksum = add_checksum(request)

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: TsmartProtocol(request_checksum, _unpack_configuration_response),
            sock=sock,
        )

        try:
            _LOGGER.debug("Sending configuration message.")
            async with asyncio.timeout(TIMEOUT):
                transport.sendto(request_checksum, (self.ip_address, UDP_PORT))
                configuration: Configuration = await protocol.done
        finally:
            transport.close()
            sock.close()

        _LOGGER.info("Received configuration from %s" % self.ip_address)

        return configuration

    # pylint:disable=too-many-locals
    async def control_read(self) -> Status:
        """Get status from the immersion heater."""

        loop = asyncio.get_running_loop()

        sock = self.create_socket()

        request = struct.pack(MESSAGE_HEADER, 0xF1, 0, 0, 0)
        request_checksum = add_checksum(request)

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: TsmartProtocol(request_checksum, _unpack_control_read_response),
            sock=sock,
        )

        try:
            _LOGGER.debug("Sending control message.")
            async with asyncio.timeout(TIMEOUT):
                transport.sendto(request_checksum, (self.ip_address, UDP_PORT))
                status: Status = await protocol.done
        finally:
            transport.close()
            sock.close()

        _LOGGER.info("Received control from %s" % self.ip_address)

        return status

    async def control_write(self, power: bool, mode: Mode, setpoint: int) -> None:
        """Set the immersion heater."""

        _LOGGER.info("Control set %d %d %0.2f" % (power, mode, setpoint))

        loop = asyncio.get_running_loop()

        sock = self.create_socket()

        request = struct.pack(
            "=BBBBHBB", 0xF2, 0, 0, 1 if power else 0, setpoint * 10, mode, 0
        )
        request_checksum = add_checksum(request)

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: TsmartProtocol(request_checksum, _unpack_control_write_response),
            sock=sock,
        )

        try:
            _LOGGER.debug("Sending control message.")
            async with asyncio.timeout(TIMEOUT):
                transport.sendto(request_checksum, (self.ip_address, UDP_PORT))
                await protocol.done
        finally:
            transport.close()
            sock.close()

        _LOGGER.info("Received control from %s" % self.ip_address)

    async def async_restart(self, offset_ms: int = 1000) -> None:
        """Restart the device after specified offset time in milliseconds."""
        if not 100 <= offset_ms <= 10000:
            raise ValueError("Offset must be between 100ms and 10000ms")

        _LOGGER.info("Restarting device %s after %dms" % (self.ip_address, offset_ms))

        loop = asyncio.get_running_loop()

        sock = self.create_socket()

        # Split offset into low and high bytes for sub-command
        sub = offset_ms & 0xFF  # Low byte
        sub2 = (offset_ms >> 8) & 0xFF  # High byte

        request = struct.pack("=BBBB", 0x02, sub, sub2, 0)

        request_checksum = add_checksum(request)

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: TsmartProtocol(request_checksum, _unpack_control_write_response),
            sock=sock,
        )

        try:
            _LOGGER.debug("Sending restart message.")
            async with asyncio.timeout(TIMEOUT):
                transport.sendto(request_checksum, (self.ip_address, UDP_PORT))
                await protocol.done
        finally:
            transport.close()
            sock.close()

        _LOGGER.info("Restart command acknowledged by %s" % self.ip_address)

    async def async_timesync(self) -> None:
        """Set the device time using UTC timestamp in milliseconds."""
        timestamp_ms = int(time.time() * 1000)

        _LOGGER.info(
            "Setting time on device %s to %d" % (self.ip_address, timestamp_ms)
        )

        loop = asyncio.get_running_loop()

        sock = self.create_socket()

        request = struct.pack("=BBBIB", 0x03, 0, 0, timestamp_ms, 0)

        request_checksum = add_checksum(request)

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: TsmartProtocol(request_checksum, _unpack_control_write_response),
            sock=sock,
        )

        try:
            _LOGGER.debug("Sending time set message.")
            async with asyncio.timeout(TIMEOUT):
                transport.sendto(request_checksum, (self.ip_address, UDP_PORT))
                await protocol.done
        finally:
            transport.close()
            sock.close()

        _LOGGER.info("Time set command acknowledged by %s" % self.ip_address)

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The TSmartClient object.
        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.
        """
