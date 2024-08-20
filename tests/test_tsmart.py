"""Asynchronous Python client for TSmart."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch

import pytest

import aiotsmart
from aiotsmart.tsmart import TSmartClient, Mode

from aiotsmart.exceptions import (
    TSmartBadResponseError,
)

if TYPE_CHECKING:
    from syrupy import SnapshotAssertion


CONFIGURATION_RESPONSE = {
    "device_id": "9B2A0D",
    "device_name": "TESLA",
    "firmware_version": "1.9.96",
    "firmware_name": "Boiler",
}


async def test_configuration_read(
    tsmart_client: TSmartClient,
    snapshot: SnapshotAssertion,
) -> None:
    """Test retrieving configuration."""

    # callback = Mock()
    # async_callback = AsyncMock()

    with patch(
        "aiotsmart.tsmart._unpack_configuration_response",
        return_value=CONFIGURATION_RESPONSE,
    ):
        assert tsmart_client.configuration_read == snapshot
    #     protocol = aiotsmart.tsmart.TsmartProtocol(callback)
    #     async_protocol = aiotsmart.tsmart.TsmartProtocol(async_callback)
    #     protocol.datagram_received(DATA, ADDR)
    #     async_protocol.datagram_received(DATA, ADDR)

    # callback.assert_called_once()
    # async_callback.assert_called_once()


# async def test_configuration_read_no_response(
#     tsmart_client: TSmartClient,
#     snapshot: SnapshotAssertion,
# ) -> None:
#     """Test retrieving no response from configuration."""

#     with patch("aiotsmart.TSmartClient._request", return_value=None):
#         with pytest.raises(TSmartBadResponseError):
#             assert await tsmart_client.configuration_read() == snapshot


# async def test_control_read(
#     tsmart_client: TSmartClient,
#     snapshot: SnapshotAssertion,
# ) -> None:
#     """Test retrieving status."""

#     with patch(
#         "aiotsmart.TSmartClient._request",
#         return_value=b"\xf1\x00\x00\x00d\x00\x00\xe0\x01\x00\x01\x1b\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x009",
#     ):
#         assert await tsmart_client.control_read() == snapshot


# async def test_control_read_no_response(
#     tsmart_client: TSmartClient,
#     snapshot: SnapshotAssertion,
# ) -> None:
#     """Test retrieving no response from status."""

#     with patch("aiotsmart.TSmartClient._request", return_value=None):
#         with pytest.raises(TSmartNoResponseError):
#             assert await tsmart_client.control_read() == snapshot


# async def test_control_set(
#     tsmart_client: TSmartClient,
# ) -> None:
#     """Test setting control."""

#     with patch("aiotsmart.TSmartClient._request", return_value=b"\xf2\x00\x00\xa7"):
#         await tsmart_client.control_write(power=True, mode=Mode.MANUAL, setpoint=15)


# async def test_control_set_no_response(
#     tsmart_client: TSmartClient,
# ) -> None:
#     """Test setting control."""

#     with patch("aiotsmart.TSmartClient._request", return_value=None):
#         with pytest.raises(TSmartNoResponseError):
#             await tsmart_client.control_write(power=True, mode=Mode.MANUAL, setpoint=15)
