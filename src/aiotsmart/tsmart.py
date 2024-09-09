"""Homeassistant Client."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
import socket
import struct
from typing import Any, Self, Callable

from aiotsmart.exceptions import (
    TSmartBadResponseError,
    TSmartCancelledError,
    TSmartTimeoutError,
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
        raw_response=data,
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

    status = Status(
        power=bool(power),
        setpoint=setpoint / 10,
        mode=Mode(mode),
        temperature_high=t_high / 10,
        temperature_low=t_low / 10,
        temperature_average=(t_high + t_low) / 20,
        relay=bool(relay),
        error_e01=(error_buffer[0] >> 7) & 1 == 1,
        error_e02=(error_buffer[2] >> 7) & 1 == 1,
        error_e03=(error_buffer[4] >> 7) & 1 == 1,
        error_e04=(error_buffer[6] >> 7) & 1 == 1,
        error_w01=(error_buffer[8] >> 7) & 1 == 1,
        error_w02=(error_buffer[10] >> 7) & 1 == 1,
        error_w03=(error_buffer[12] >> 7) & 1 == 1,
        error_e05=(error_buffer[14] >> 7) & 1 == 1,
        raw_response=data,
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
        except asyncio.TimeoutError as ex:
            raise TSmartTimeoutError() from ex
        except asyncio.CancelledError as ex:
            raise TSmartCancelledError() from ex

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
        except asyncio.TimeoutError as ex:
            raise TSmartTimeoutError() from ex

        except asyncio.CancelledError as ex:
            raise TSmartCancelledError() from ex

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
        except asyncio.TimeoutError as ex:
            raise TSmartTimeoutError() from ex

        except asyncio.CancelledError as ex:
            raise TSmartCancelledError() from ex

        finally:
            transport.close()
            sock.close()

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
