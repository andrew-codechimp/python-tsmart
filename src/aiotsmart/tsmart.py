"""Homeassistant Client."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from importlib import metadata
import logging
import socket
import struct
from typing import Any, Self, Callable

from aiotsmart.exceptions import (
    TSmartBadResponseError,
)
from aiotsmart.models import Configuration, Mode, Status
from aiotsmart.util import validate_checksum, add_checksum

from .const import MESSAGE_HEADER

VERSION = metadata.version(__package__)

UDP_PORT = 1337
DISCOVERY_INTERVAL = 2  # seconds
CONFIGURATION_MESSAGE = struct.pack(MESSAGE_HEADER, 0x01, 0, 0, 0x01 ^ 0x55)
BROADCAST_ADDR = ("255.255.255.255", UDP_PORT)

_LOGGER = logging.getLogger(__name__)


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
        error,
        checksum,
    ) = response_struct.unpack(data)

    status = Status(
        power=bool(power),
        setpoint=setpoint / 10,
        mode=Mode(mode),
        temperature_high=t_high / 10,
        temperature_low=t_low / 10,
        temperature_average=(t_high + t_low) / 20,
        relay=bool(relay),
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

    async def configuration_read(self) -> Configuration:
        """Get configuration from immersion heater."""

        loop = asyncio.get_running_loop()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet, UDP

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(("", 1337))
        sock.connect((self.ip_address, UDP_PORT))

        request = struct.pack(MESSAGE_HEADER, 0x21, 0, 0, 0)
        request_checksum = add_checksum(request)

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: TsmartProtocol(request_checksum, _unpack_configuration_response),
            sock=sock,
        )

        try:
            _LOGGER.debug("Sending configuration message.")
            transport.sendto(request_checksum, (self.ip_address, UDP_PORT))
            configuration: Configuration = await protocol.done

        except asyncio.CancelledError:
            _LOGGER.debug("Cancelling TSmart configuration task")
            transport.close()

        finally:
            transport.close()

        _LOGGER.info("Received configuration from %s" % self.ip_address)

        return configuration

    # pylint:disable=too-many-locals
    async def control_read(self) -> Status:
        """Get status from the immersion heater."""

        loop = asyncio.get_running_loop()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet, UDP

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(("", 1337))
        sock.connect((self.ip_address, UDP_PORT))

        request = struct.pack(MESSAGE_HEADER, 0xF1, 0, 0, 0)
        request_checksum = add_checksum(request)

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: TsmartProtocol(request_checksum, _unpack_control_read_response),
            sock=sock,
        )

        try:
            _LOGGER.debug("Sending control message.")
            transport.sendto(request_checksum, (self.ip_address, UDP_PORT))
            status: Status = await protocol.done

        except asyncio.CancelledError:
            _LOGGER.debug("Cancelling TSmart control task")
            transport.close()

        finally:
            transport.close()

        _LOGGER.info("Received control from %s" % self.ip_address)

        return status

    async def control_write(self, power: bool, mode: Mode, setpoint: int) -> None:
        """Set the immersion heater."""

        _LOGGER.info("Control set %d %d %0.2f" % (power, mode, setpoint))

        loop = asyncio.get_running_loop()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet, UDP

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(("", 1337))
        sock.connect((self.ip_address, UDP_PORT))

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
            transport.sendto(request_checksum, (self.ip_address, UDP_PORT))
            await protocol.done

        except asyncio.CancelledError:
            _LOGGER.debug("Cancelling TSmart control task")
            transport.close()

        finally:
            transport.close()

        _LOGGER.info("Received control from %s" % self.ip_address)

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
