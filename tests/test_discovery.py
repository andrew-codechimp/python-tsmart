"""Asynchronous Python client for TSmart."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

import aiotsmart
import aiotsmart.discovery

if TYPE_CHECKING:
    from syrupy import SnapshotAssertion

ADDR = ("192.168.1.1", 1337)
DATA = b"\x01\x00\x00 \x00\r*\x9b\x00TESLA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\xe3"
BAD_DATA = b"\x05\x00\x09 \x09\r*\x9b\x00TESLA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\xe3"
RESPONSE = {"ip_address": "192.168.1.35", "device_id": "9B2A0D", "device_name": "TESLA"}

# pylint: disable=C0103
# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_discovery_unpack() -> None:
    """Test device discovery unpack."""

    # pylint:disable=protected-access
    assert aiotsmart.discovery._unpack_discovery_response(DATA, ADDR)
    assert not aiotsmart.discovery._unpack_discovery_response(BAD_DATA, ADDR)


async def test_discovery(
    snapshot: SnapshotAssertion,
) -> None:
    """Test discovery."""
    with patch("aiotsmart.discovery._unpack_discovery_response", return_value=RESPONSE):
        assert aiotsmart.TSmartDiscovery.discover == snapshot
    #     protocol = pysqueezebox.discovery.ServerDiscoveryProtocol(callback)
    #     async_protocol = pysqueezebox.discovery.ServerDiscoveryProtocol(async_callback)
    #     protocol.datagram_received(ADDR, DATA)
    #     async_protocol.datagram_received(ADDR, DATA)

    # callback.assert_called_once()
    # async_callback.assert_called_once()

    # with patch(
    #     "aiotsmart.TSmartDiscovery._request",
    #     return_value=b"!\x00\x00 \x00\r*\x9b\x00TESLA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\x00\x01\t`Boiler\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\xff\xff\x01\x01\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\xff\xff\xff\xff\x00\x00wifissid\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00wifipassword\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd0!\xf9\xb1\xd6QTESLA_74BA1D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x01\xa7\x1e\x00\x00\x00\x00\x00\x04d\x00\t\x00\x00\x00\x01\x00\x00\x00n",
    # ):
    #     assert await tsmart_client.configuration_read() == snapshot