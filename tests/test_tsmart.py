"""Asynchronous Python client for TSmart."""

from __future__ import annotations

from typing import TYPE_CHECKING
import pytest

import aiotsmart

from aiotsmart.exceptions import TSmartBadResponseError
from aiotsmart.models import Mode, Status
import aiotsmart.tsmart
from aiotsmart.util import add_checksum

if TYPE_CHECKING:
    from syrupy import SnapshotAssertion

CONFIGURATION_REQUEST = bytearray(b"!\x00\x00t")
CONFIGURATION_DATA = bytearray(
    b"!\x00\x00 \x00\r*\x9b\x00TESLA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\x00\x01\t`Boiler\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\xff\xff\x01\x01\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\xff\xff\xff\xff\x00\x00abcdefghijklmnopq\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00abcdefghijkl\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd0!\xf9\xb1\xd6QTESLA_9B2A0D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x01\xa7\x1e\x00\x00\x00\x00\x00\x04d\x00\t\x00\x00\x00\x01\x00\x00\x00t"
)
BAD_CONFIGURATION_DATA = bytearray(
    b"!\x00\x00 \x00\r*\x9b\x00XESLA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\x00\x01\t`Boiler\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\xff\xff\x01\x01\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\xff\xff\xff\xff\x00\x00abcdefghijklmnopq\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00abcdefghijkl\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd0!\xf9\xb1\xd6QTESLA_9B2A0D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x01\xa7\x1e\x00\x00\x00\x00\x00\x04d\x00\t\x00\x00\x00\x01\x00\x00\x00t"
)

CONFIGURATION_RESPONSE = {
    "device_id": "9B2A0D",
    "device_name": "TESLA",
    "firmware_version": "1.9.96",
    "firmware_name": "Boiler",
}

CONTROL_READ_REQUEST = bytearray(b"\xf1\x00\x00\xa4")
CONTROL_READ_DATA = bytearray(
    b"\xf1\x00\x00\x00d\x00\x00\x1d\x02\x00\x01\x1a\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6"
)
BAD_CONTROL_READ_DATA = bytearray(
    b"\xf1\x00\x00\x00d\x00\x00\x1a\x02\x00\x01\x1a\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc6"
)

CONTROL_WRITE_DATA = bytearray(b"\xf2\x00\x00\xa7")
BAD_CONTROL_WRITE_DATA = bytearray(b"\xf1\x00\x00\xa7")


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
    status = aiotsmart.tsmart._unpack_control_read_response(
        CONTROL_READ_REQUEST, CONTROL_READ_DATA
    )
    assert status
    assert not status.has_error

    # pylint:disable=protected-access
    with pytest.raises(TSmartBadResponseError):
        assert aiotsmart.tsmart._unpack_control_read_response(
            CONTROL_READ_REQUEST, BAD_CONTROL_READ_DATA
        )


async def test_control_write_unpack_success() -> None:
    """Test control write unpack with successful response."""
    # pylint:disable=protected-access
    aiotsmart.tsmart._unpack_control_write_response(bytearray(), CONTROL_WRITE_DATA)
    # Success case - function should not raise an exception


async def test_control_write_unpack_failure() -> None:
    """Test control write unpack with bad response."""
    # pylint:disable=protected-access
    with pytest.raises(TSmartBadResponseError):
        aiotsmart.tsmart._unpack_control_write_response(
            bytearray(), BAD_CONTROL_WRITE_DATA
        )


async def test_configuration_unpack_wrong_length() -> None:
    """Test configuration unpack with wrong packet length."""
    # pylint:disable=protected-access
    short_data = b"short"
    with pytest.raises(TSmartBadResponseError, match="Unexpected packet length"):
        aiotsmart.tsmart._unpack_configuration_response(
            CONFIGURATION_REQUEST, short_data
        )


async def test_configuration_unpack_error_response() -> None:
    """Test configuration unpack with error response."""
    # pylint:disable=protected-access
    error_data = bytearray(CONFIGURATION_DATA)
    error_data[0] = 0  # Set error code
    with pytest.raises(TSmartBadResponseError, match="Got error response"):
        aiotsmart.tsmart._unpack_configuration_response(
            CONFIGURATION_REQUEST, error_data
        )


async def test_configuration_unpack_wrong_response_type() -> None:
    """Test configuration unpack with wrong response type."""
    # pylint:disable=protected-access
    wrong_data = bytearray(CONFIGURATION_DATA)
    wrong_data[0] = 0x22  # Different response type
    with pytest.raises(TSmartBadResponseError, match="Unexpected response type"):
        aiotsmart.tsmart._unpack_configuration_response(
            CONFIGURATION_REQUEST, wrong_data
        )


async def test_control_read_unpack_wrong_length() -> None:
    """Test control read unpack with wrong packet length."""
    # pylint:disable=protected-access
    short_data = b"short"
    with pytest.raises(TSmartBadResponseError, match="Unexpected packet length"):
        aiotsmart.tsmart._unpack_control_read_response(CONTROL_READ_REQUEST, short_data)


async def test_control_read_unpack_error_response() -> None:
    """Test control read unpack with error response."""
    # pylint:disable=protected-access
    error_data = bytearray(CONTROL_READ_DATA)
    error_data[0] = 0  # Set error code
    with pytest.raises(TSmartBadResponseError, match="Got error response"):
        aiotsmart.tsmart._unpack_control_read_response(CONTROL_READ_REQUEST, error_data)


async def test_control_read_unpack_wrong_response_type() -> None:
    """Test control read unpack with wrong response type."""
    # pylint:disable=protected-access
    wrong_data = bytearray(CONTROL_READ_DATA)
    wrong_data[0] = 0x22  # Different response type
    with pytest.raises(TSmartBadResponseError, match="Unexpected response type"):
        aiotsmart.tsmart._unpack_control_read_response(CONTROL_READ_REQUEST, wrong_data)


async def test_status_has_error_with_errors() -> None:
    """Test status has_error property with various error conditions."""
    # Create a Status object with errors directly

    status = Status(
        power=True,
        setpoint=22,
        mode=Mode.ECO,
        temperature_high=25,
        temperature_low=20,
        temperature_average=22,
        relay=False,
        error_e01=True,  # Set an error
        error_e02=False,
        error_e03=False,
        error_e04=False,
        error_e05=False,
        error_w01=False,
        error_w02=False,
        error_w03=False,
        raw_response=b"test_data",
    )

    assert status.has_error is True

    # Test with no errors
    status_no_errors = Status(
        power=True,
        setpoint=22,
        mode=Mode.ECO,
        temperature_high=25,
        temperature_low=20,
        temperature_average=22,
        relay=False,
        error_e01=False,
        error_e02=False,
        error_e03=False,
        error_e04=False,
        error_e05=False,
        error_w01=False,
        error_w02=False,
        error_w03=False,
        raw_response=b"test_data",
    )

    assert status_no_errors.has_error is False


async def test_tsmart_protocol_datagram_received() -> None:
    """Test TsmartProtocol datagram_received method."""

    def mock_unpack(_request: bytearray, _data: bytes) -> dict[str, str]:  # pylint: disable=unused-argument
        return {"test": "response"}

    protocol = aiotsmart.tsmart.TsmartProtocol(bytearray(b"test"), mock_unpack)

    # Simulate receiving data
    protocol.datagram_received(b"test_data", ("192.168.1.1", 1337))

    # Check that the future is set
    assert protocol.done.done()
    assert protocol.done.result() == {"test": "response"}
