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
import aiotsmart.tsmart
from aiotsmart.util import add_checksum

if TYPE_CHECKING:
    from syrupy import SnapshotAssertion

CONFIGURATION_REQUEST = b"!\x00\x00t"
CONFIGURATION_DATA = b"!\x00\x00 \x00\r*\x9b\x00TESLA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\x00\x01\t`Boiler\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\xff\xff\x01\x01\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\xff\xff\xff\xff\x00\x00abcdefghijklmnopq\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00abcdefghijkl\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd0!\xf9\xb1\xd6QTESLA_9B2A0D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x01\xa7\x1e\x00\x00\x00\x00\x00\x04d\x00\t\x00\x00\x00\x01\x00\x00\x00t"
BAD_CONFIGURATION_DATA = b"!\x00\x00 \x00\r*\x9b\x00XESLA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\x00\x01\t`Boiler\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\xff\xff\x01\x01\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\xff\xff\xff\xff\x00\x00abcdefghijklmnopq\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00abcdefghijkl\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd0!\xf9\xb1\xd6QTESLA_9B2A0D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x01\xa7\x1e\x00\x00\x00\x00\x00\x04d\x00\t\x00\x00\x00\x01\x00\x00\x00t"

CONFIGURATION_RESPONSE = {
    "device_id": "9B2A0D",
    "device_name": "TESLA",
    "firmware_version": "1.9.96",
    "firmware_name": "Boiler",
}

CONTROL_READ_REQUEST = b"\xf1\x00\x00\xa4"
CONTROL_READ_DATA = b"\xf1\x00\x00\x00d\x00\x00\x1d\x02\x00\x01\x1a\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6"
BAD_CONTROL_READ_DATA = b"\xf1\x00\x00\x00d\x00\x00\x1a\x02\x00\x01\x1a\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6"

CONTROL_WRITE_DATA = b"\xf2\x00\x00\xa7"
BAD_CONTROL_WRITE_DATA = b"\xf1\x00\x00\xa7"


async def test_add_checksum() -> None:
    """Test adding a checksum"""
    assert add_checksum(b"\xf1\x00\x00\x00") == b"\xf1\x00\x00\xa4"


async def test_configuration_unpack(
    snapshot: SnapshotAssertion,
) -> None:
    """Test configuration unpack."""

    # pylint:disable=protected-access
    assert (
        aiotsmart.tsmart._unpack_configuration_response(
            CONFIGURATION_REQUEST, CONFIGURATION_DATA
        )
        == snapshot
    )

    # pylint:disable=protected-access
    with pytest.raises(TSmartBadResponseError):
        assert aiotsmart.tsmart._unpack_configuration_response(
            CONFIGURATION_REQUEST, BAD_CONFIGURATION_DATA
        )

    # assert not aiotsmart.tsmart._unpack_configuration_response(
    #     CONFIGURATION_REQUEST, BAD_CONFIGURATION_DATA
    # )


async def test_control_read_unpack(
    snapshot: SnapshotAssertion,
) -> None:
    """Test control read unpack."""

    # pylint:disable=protected-access
    assert (
        aiotsmart.tsmart._unpack_control_read_response(
            CONTROL_READ_REQUEST, CONTROL_READ_DATA
        )
        == snapshot
    )

    # pylint:disable=protected-access
    assert not aiotsmart.tsmart._unpack_control_read_response(
        CONTROL_READ_REQUEST, CONTROL_READ_DATA
    ).has_error

    # pylint:disable=protected-access
    with pytest.raises(TSmartBadResponseError):
        assert aiotsmart.tsmart._unpack_control_read_response(
            CONTROL_READ_REQUEST, BAD_CONTROL_READ_DATA
        )


async def test_control_write_unpack(
    snapshot: SnapshotAssertion,
) -> None:
    """Test control write unpack."""

    # pylint:disable=protected-access
    assert (
        aiotsmart.tsmart._unpack_control_write_response(None, CONTROL_WRITE_DATA)
        == snapshot
    )

    # pylint:disable=protected-access
    with pytest.raises(TSmartBadResponseError):
        assert aiotsmart.tsmart._unpack_control_write_response(
            None, BAD_CONTROL_WRITE_DATA
        )


# async def test_configuration_read(
#     tsmart_client: TSmartClient,
#     snapshot: SnapshotAssertion,
# ) -> None:
#     """Test retrieving configuration."""

#     # callback = Mock()
#     # async_callback = AsyncMock()

#     with patch(
#         "aiotsmart.tsmart._unpack_configuration_response",
#         return_value=CONFIGURATION_RESPONSE,
#     ):
#         assert tsmart_client.configuration_read == snapshot


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
#         "aiotsmart.tsmart._unpack_control_read_response",
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
