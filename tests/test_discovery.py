"""Asynchronous Python client for TSmart."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch
import logging

import pytest

import aiotsmart
from aiotsmart.discovery import TSmartDiscovery

if TYPE_CHECKING:
    from syrupy import SnapshotAssertion

ADDR = ("192.168.1.1", 1337)
DATA = b"\x01\x00\x00 \x00\r*\x9b\x00TESLA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\xe3"
BAD_DATA = b"\x05\x00\x09 \x09\r*\x9b\x00TESLA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\xe3"
RESPONSE = {"ip_address": "192.168.1.35", "device_id": "9B2A0D", "device_name": "TESLA"}
BAD_RESPONSE = {"ip_address": "192.168.1.35", "device_id": "9B2A0D"}

# pylint: disable=C0103
# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio
tsmart_logger = logging.getLogger("pysqueezebox.discovery")


async def test_discovery_unpack() -> None:
    """Test device discovery unpack."""

    # pylint:disable=protected-access
    assert aiotsmart.discovery._unpack_discovery_response(DATA, ADDR)
    assert not aiotsmart.discovery._unpack_discovery_response(BAD_DATA, ADDR)


async def test_discovery(
    tsmart_discovery: TSmartDiscovery,
    snapshot: SnapshotAssertion,
) -> None:
    """Test discovery."""

    callback = Mock()
    async_callback = AsyncMock()

    with patch("aiotsmart.discovery._unpack_discovery_response", return_value=RESPONSE):
        assert tsmart_discovery.discover == snapshot
        protocol = aiotsmart.discovery.DiscoveryProtocol(callback)
        async_protocol = aiotsmart.discovery.DiscoveryProtocol(async_callback)
        protocol.datagram_received(DATA, ADDR)
        async_protocol.datagram_received(DATA, ADDR)

    callback.assert_called_once()
    async_callback.assert_called_once()


# async def test_bad_response():
#     """Test handling of a non TSmart discovery response."""

#     with patch(
#         "aiotsmart.discovery._unpack_discovery_response", return_value=BAD_RESPONSE
#     ), patch.object(tsmart_logger, "info") as logger:
#         test_protocol = aiotsmart.discovery.DiscoveryProtocol(None)
#         test_protocol.datagram_received(ADDR, BAD_DATA)
#         logger.assert_called_once()
