"""Homeassistant Client."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from importlib import metadata
import logging
import socket
import struct
from typing import cast, Self

import asyncio_dgram
from asyncio_dgram.aio import DatagramClient, DatagramServer

from aiotsmart.exceptions import (
    TSmartConnectionError,
    TSmartNoResponseError,
    TSmartNotFoundError,
    TSmartTimeoutError,
)
from aiotsmart.models import Configuration, Mode, Status, Discovery

VERSION = metadata.version(__package__)

UDP_PORT = 1337

_LOGGER = logging.getLogger(__name__)


@dataclass
class TSmartClient:
    """TSmart Client."""

    ip: str | None = None

    # pylint:disable=too-many-locals
    async def discover(
        self, stop_on_first: bool = False, tries: int = 2, timeout: int = 2
    ) -> list[Discovery]:
        """Broadcast discovery packet."""
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )  # Internet, UDP

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        sock.bind(("", UDP_PORT))

        _LOGGER.info("Performing discovery")

        stream = cast(DatagramServer, await asyncio_dgram.from_socket(sock))
        response_struct = struct.Struct("=BBBHL32sBB")

        devices = {}

        data = None
        for _ in range(tries):
            message = struct.pack("=BBBB", 0x01, 0, 0, 0x01 ^ 0x55)

            await stream.send(data=message, addr=("255.255.255.255", UDP_PORT))

            _LOGGER.info("Discovery message sent")

            while True:
                try:
                    data, remote_addr = await asyncio.wait_for(stream.recv(), timeout)
                    remote_addr_ip = cast(tuple[str, int], remote_addr)[0]

                    if len(data) == len(message):
                        # Got our own broadcast
                        continue

                    if len(data) != response_struct.size:
                        _LOGGER.warning(
                            "Unexpected packet length (got: %d, expected: %d)"
                            % (len(data), response_struct.size)
                        )
                        continue

                    if data[0] == 0:
                        _LOGGER.warning("Got error response (code %d)" % (data[0]))
                        continue

                    if (
                        data[0] != message[0]
                        or data[1] != data[1]
                        or data[2] != data[2]
                    ):
                        _LOGGER.warning(
                            "Unexpected response type (%02X %02X %02X)"
                            % (data[0], data[1], data[2])
                        )
                        continue

                    t = 0
                    for b in data[:-1]:
                        t = t ^ b
                    if t ^ 0x55 != data[-1]:
                        _LOGGER.warning("Received packet checksum failed")
                        continue

                    _LOGGER.info("Got response from %s", remote_addr_ip)

                    # pylint:disable=unused-variable
                    if remote_addr_ip not in devices:
                        (
                            cmd,
                            sub,
                            sub2,
                            device_type,
                            device_id,
                            name,
                            tz,
                            checksum,
                        ) = response_struct.unpack(data)
                        device_name = name.decode("utf-8").split("\x00")[0]
                        device_id_str = f"{device_id:04X}"
                        _LOGGER.info("Discovered %s %s" % (device_id_str, device_name))
                        devices[remote_addr_ip] = Discovery(
                            remote_addr_ip, device_id_str, device_name
                        )
                        if stop_on_first:
                            break

                except asyncio.exceptions.TimeoutError:
                    break

            if stop_on_first and len(devices) > 0:
                break

        stream.close()
        sock.close()

        return list(devices.values())

    async def _request(self, request: bytes, response_struct: struct.Struct) -> bytes:
        assert self.ip is not None

        t = 0
        request = bytearray(request)
        for b in request[:-1]:
            t = t ^ b
        request[-1] = t ^ 0x55

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet, UDP

            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", 1337))
            sock.connect((self.ip, UDP_PORT))

            stream = cast(DatagramClient, await asyncio_dgram.from_socket(sock))
        except OSError as exception:
            msg = exception.strerror
            if exception.errno == 8:
                raise TSmartNotFoundError(msg) from exception
            if exception.errno == 48:
                msg = "Unable to connect to socket"
            raise TSmartConnectionError(msg) from exception

        data = None
        for _ in range(2):
            await stream.send(data=request)

            _LOGGER.info("Message sent to %s" % self.ip)

            try:
                data, _ = await asyncio.wait_for(stream.recv(), 2)
                if len(data) != response_struct.size:
                    _LOGGER.warning(
                        "Unexpected packet length (got: %d, expected: %d)"
                        % (len(data), response_struct.size)
                    )
                    continue

                if data[0] == 0:
                    _LOGGER.warning("Got error response (code %d)" % (data[0]))
                    continue

                if data[0] != request[0] or data[1] != data[1] or data[2] != data[2]:
                    _LOGGER.warning(
                        "Unexpected response type (%02X %02X %02X)"
                        % (data[0], data[1], data[2])
                    )
                    continue

                if not self._validate_checksum(data):
                    _LOGGER.warning("Received packet checksum failed")

            except asyncio.exceptions.TimeoutError:
                continue

            break

        stream.close()
        sock.close()

        if data is None:
            raise TSmartTimeoutError(
                "Timeout occurred while connecting to immersion heater"
            )

        return data

    def _validate_checksum(self, data: bytes) -> bool:
        """Validate the checksum."""

        t = 0
        for b in data[:-1]:
            t = t ^ b
        return t ^ 0x55 == data[-1]

    async def configuration_read(self) -> Configuration:
        """Get configuration from immersion heater."""

        _LOGGER.info("Async get configuration")
        request = struct.pack("=BBBB", 0x21, 0, 0, 0)

        response_struct = struct.Struct("=BBBHL32sBBBBB32s28s32s64s124s")
        response = await self._request(request, response_struct)

        if response is None:
            raise TSmartNoResponseError("No response received")

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
        ) = response_struct.unpack(response)

        configuration = Configuration(
            device_id=f"{device_id:04X}",
            device_name=device_name.decode("utf-8").split("\x00")[0],
            firmware_version=f"{firmware_version_major}.{firmware_version_minor}.{firmware_version_deployment}",
            firmware_name=firmware_name.decode("utf-8").split("\x00")[0],
        )

        _LOGGER.info("Received configuration from %s" % self.ip)

        return configuration

    # pylint:disable=too-many-locals
    async def control_read(self) -> Status:
        """Get status from the immersion heater."""

        _LOGGER.info("Async get status")
        request = struct.pack("=BBBB", 0xF1, 0, 0, 0)

        response_struct = struct.Struct("=BBBBHBHBBH16sB")
        response = await self._request(request, response_struct)

        if response is None:
            raise TSmartNoResponseError("No response received")

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
        ) = response_struct.unpack(response)

        status = Status(
            power=bool(power),
            setpoint=setpoint / 10,
            mode=Mode(mode),
            temperature_high=t_high / 10,
            temperature_low=t_low / 10,
            temperature_average=(t_high + t_low) / 20,
            relay=bool(relay),
        )

        _LOGGER.info("Received status from %s" % self.ip)

        return status

    async def control_write(self, power: bool, mode: Mode, setpoint: int) -> None:
        """Set the immersion heater."""

        _LOGGER.info("Async control set %d %d %0.2f" % (power, mode, setpoint))

        request = struct.pack(
            "=BBBBHBB", 0xF2, 0, 0, 1 if power else 0, setpoint * 10, mode, 0
        )

        response_struct = struct.Struct("=BBBB")
        response = await self._request(request, response_struct)
        if response != b"\xf2\x00\x00\xa7":
            raise TSmartNoResponseError

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
