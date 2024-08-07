"""TSmart Discovery."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import logging
import socket
import struct
from typing import Any, Callable

from aiotsmart.models import DiscoveredDevice
from aiotsmart.util import validate_checksum

from .const import MESSAGE_HEADER

UDP_PORT = 1337
DISCOVERY_INTERVAL = 2  # seconds
DISCOVERY_MESSAGE = struct.pack(MESSAGE_HEADER, 0x01, 0, 0, 0x01 ^ 0x55)
BROADCAST_ADDR = ("255.255.255.255", UDP_PORT)

_LOGGER = logging.getLogger(__name__)

SHARED_LIST: list[DiscoveredDevice] = []


def _unpack_discovery_response(
    data: bytes, addr: tuple[str, int]
) -> dict[str, str] | None:
    """Return dict of unpacked responses from TSmart Immersion Heater."""
    response_struct = struct.Struct("=BBBHL32sBB")

    remote_addr_ip_address = addr[0]

    result = {"ip_address": addr[0]}

    if len(data) == len(DISCOVERY_MESSAGE):
        # Got our own broadcast
        return None

    if len(data) != response_struct.size:
        _LOGGER.debug(
            "Unexpected packet length (got: %d, expected: %d)"
            % (len(data), response_struct.size)
        )
        return None

    if data[0] == 0:
        _LOGGER.debug("Got error response (code %d)" % (data[0]))
        return None

    if data[0] != DISCOVERY_MESSAGE[0]:
        _LOGGER.debug(
            "Unexpected response type (%02X %02X %02X)" % (data[0], data[1], data[2])
        )
        return None

    if not validate_checksum(data):
        _LOGGER.debug("Received packet checksum failed")
        return None

    _LOGGER.debug("Got response from %s", remote_addr_ip_address)

    # pylint:disable=unused-variable
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

    result["device_name"] = name.decode("utf-8").split("\x00")[0]
    result["device_id"] = f"{device_id:04X}"
    _LOGGER.info("Discovered %s %s" % (result["device_id"], result["device_name"]))

    return result


class DiscoveryProtocol(asyncio.DatagramProtocol):
    """Protocol to send discovery request and receive responses."""

    def __init__(self, callback: Callable[[DiscoveredDevice], None]) -> None:
        """Initialize with callback function."""
        self.transport = None
        self.callback = callback

    def connection_made(self, transport: Any) -> None:
        """Connect to transport."""
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        """Test if responder is a TSmart Immersion Heater."""
        _LOGGER.debug("Received discovery response from %s", addr)
        response = _unpack_discovery_response(data, addr)
        if response:
            if (
                "ip_address" not in response
                or "device_name" not in response
                or "device_id" not in response
            ):
                _LOGGER.info(
                    "TSmart discovery response %s does not contain enough information to connect",
                    response,
                )
            if callable(self.callback):
                result = self.callback(
                    DiscoveredDevice(
                        response["ip_address"],
                        response["device_id"],
                        response["device_name"],
                    )
                )
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)


@dataclass
class TSmartDiscovery:
    """TSmart Discovery."""

    _discovered_devices: list[DiscoveredDevice] = field(
        default_factory=lambda: SHARED_LIST
    )

    def _device_discovered(self, device: DiscoveredDevice) -> None:
        """Add device to discover list if new."""

        matched_device: DiscoveredDevice | None = next(
            (x for x in self._discovered_devices if x.ip_address == device.ip_address),
            None,
        )

        if not matched_device:
            self._discovered_devices.append(device)

    async def discover(self) -> list[DiscoveredDevice]:
        """Broadcast discovery packet and return a list of discovered devices."""
        loop = asyncio.get_running_loop()

        sock = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )  # Internet, UDP

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        sock.bind(("", UDP_PORT))

        # One protocol instance will be created to serve all client requests
        transport, _ = await loop.create_datagram_endpoint(
            lambda: DiscoveryProtocol(self._device_discovered),
            sock=sock,
        )

        try:
            for _ in range(2):
                _LOGGER.debug("Sending discovery message.")
                transport.sendto(DISCOVERY_MESSAGE, BROADCAST_ADDR)
                await asyncio.sleep(DISCOVERY_INTERVAL)

        except asyncio.CancelledError:
            _LOGGER.debug("Cancelling TSmart discovery task")
            transport.close()

        finally:
            transport.close()

        return self._discovered_devices
