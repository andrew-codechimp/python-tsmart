"""Asynchronous Python client for TSmart."""

from __future__ import annotations

import asyncio
import struct
from typing import TYPE_CHECKING, Any
import pytest

import aiotsmart

from aiotsmart.exceptions import TSmartBadResponseError
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


async def test_async_restart(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test async_restart method."""
    client = aiotsmart.TSmartClient("192.168.1.100")

    # Track the sent data
    sent_data = []
    sent_address = []

    original_protocol_init = aiotsmart.tsmart.TsmartProtocol.__init__

    def mock_protocol_init(
        self: aiotsmart.tsmart.TsmartProtocol, request: bytearray, unpack_function: Any
    ) -> None:
        original_protocol_init(self, request, unpack_function)
        # Immediately complete the future to simulate successful response
        asyncio.get_running_loop().call_soon(self.done.set_result, None)

    class MockTransport:
        """Mock transport for testing."""

        def sendto(self, data: bytes, addr: tuple[str, int]) -> None:
            """Mock sendto method."""
            sent_data.append(data)
            sent_address.append(addr)

        def close(self) -> None:
            """Mock close method."""

    async def mock_create_endpoint(
        factory: Any, **_kwargs: Any
    ) -> tuple[MockTransport, aiotsmart.tsmart.TsmartProtocol]:
        protocol = factory()
        return MockTransport(), protocol

    # Patch the protocol init and create_datagram_endpoint
    monkeypatch.setattr(aiotsmart.tsmart.TsmartProtocol, "__init__", mock_protocol_init)
    loop = asyncio.get_running_loop()
    monkeypatch.setattr(loop, "create_datagram_endpoint", mock_create_endpoint)

    # Test with default offset
    await client.async_restart()

    # Verify the request format
    assert len(sent_data) == 1
    assert sent_address[0] == ("192.168.1.100", 1337)

    # Check the command structure: [0x02, low_byte, high_byte, checksum]
    # For 1000ms (0x03E8): low=0xE8, high=0x03
    request = sent_data[0]
    assert len(request) == 4  # 3 data bytes + 1 checksum
    assert request[0] == 0x02  # Restart command
    assert request[1] == 0xE8  # Low byte of 1000 (default)
    assert request[2] == 0x03  # High byte of 1000
    # request[3] is the checksum

    # Test with custom offset
    sent_data.clear()
    sent_address.clear()
    await client.async_restart(offset_ms=5000)

    # For 5000ms (0x1388): low=0x88, high=0x13
    request = sent_data[0]
    assert request[0] == 0x02
    assert request[1] == 0x88  # Low byte of 5000
    assert request[2] == 0x13  # High byte of 5000
    # request[3] is the checksum


async def test_async_restart_invalid_offset() -> None:
    """Test async_restart with invalid offset values."""
    client = aiotsmart.TSmartClient("192.168.1.100")

    # Test offset too small
    with pytest.raises(ValueError, match="Offset must be between 100ms and 10000ms"):
        await client.async_restart(offset_ms=50)

    # Test offset too large
    with pytest.raises(ValueError, match="Offset must be between 100ms and 10000ms"):
        await client.async_restart(offset_ms=20000)


async def test_async_timesync(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test async_timesync method."""
    client = aiotsmart.TSmartClient("192.168.1.100")

    # Mock time.time() to return a known value that fits in 32-bit milliseconds
    # Using a smaller timestamp that fits in 32-bit unsigned int when converted to milliseconds
    mock_time = 4294967.0  # This gives ~4294967000 ms, which fits in 32-bit
    monkeypatch.setattr("time.time", lambda: mock_time)

    # Track the sent data
    sent_data = []
    sent_address = []

    original_protocol_init = aiotsmart.tsmart.TsmartProtocol.__init__

    def mock_protocol_init(
        self: aiotsmart.tsmart.TsmartProtocol, request: bytearray, unpack_function: Any
    ) -> None:
        original_protocol_init(self, request, unpack_function)
        # Immediately complete the future to simulate successful response
        asyncio.get_running_loop().call_soon(self.done.set_result, None)

    class MockTransport:
        """Mock transport for testing."""

        def sendto(self, data: bytes, addr: tuple[str, int]) -> None:
            """Mock sendto method."""
            sent_data.append(data)
            sent_address.append(addr)

        def close(self) -> None:
            """Mock close method."""

    async def mock_create_endpoint(
        factory: Any, **_kwargs: Any
    ) -> tuple[MockTransport, aiotsmart.tsmart.TsmartProtocol]:
        protocol = factory()
        return MockTransport(), protocol

    # Patch the protocol init and create_datagram_endpoint
    monkeypatch.setattr(aiotsmart.tsmart.TsmartProtocol, "__init__", mock_protocol_init)
    loop = asyncio.get_running_loop()
    monkeypatch.setattr(loop, "create_datagram_endpoint", mock_create_endpoint)

    # Test timesync
    await client.async_timesync()

    # Verify the request format
    assert len(sent_data) == 1
    assert sent_address[0] == ("192.168.1.100", 1337)

    # Check the command structure: [0x03, 0x00, 0x00, timestamp_ms (4 bytes), checksum]
    request = sent_data[0]
    assert len(request) == 8  # 3 bytes + 4 byte timestamp + 1 checksum
    assert request[0] == 0x03  # Timesync command
    assert request[1] == 0x00
    assert request[2] == 0x00

    # Extract timestamp from bytes 3-6 (little-endian unsigned int)
    # The last byte (request[7]) is the checksum
    timestamp_ms = struct.unpack("<I", request[3:7])[0]
    expected_timestamp_ms = int(mock_time * 1000)
    assert timestamp_ms == expected_timestamp_ms
