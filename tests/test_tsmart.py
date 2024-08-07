"""Asynchronous Python client for TSmart."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from aiotsmart.exceptions import (
    TSmartNoResponseError,
)
from aiotsmart.tsmart import TSmartClient, Mode

if TYPE_CHECKING:
    from syrupy import SnapshotAssertion


async def test_configuration_read(
    tsmart_client: TSmartClient,
    snapshot: SnapshotAssertion,
) -> None:
    """Test retrieving configuration."""

    with patch(
        "aiotsmart.TSmartClient._request",
        return_value=b"!\x00\x00 \x00\r*\x9b\x00TESLA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\x00\x01\t`Boiler\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\xff\xff\x01\x01\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\xff\xff\xff\xff\x00\x00wifissid\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00wifipassword\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd0!\xf9\xb1\xd6QTESLA_74BA1D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x01\xa7\x1e\x00\x00\x00\x00\x00\x04d\x00\t\x00\x00\x00\x01\x00\x00\x00n",
    ):
        assert await tsmart_client.configuration_read() == snapshot


async def test_configuration_read_no_response(
    tsmart_client: TSmartClient,
    snapshot: SnapshotAssertion,
) -> None:
    """Test retrieving no response from configuration."""

    with patch("aiotsmart.TSmartClient._request", return_value=None):
        with pytest.raises(TSmartNoResponseError):
            assert await tsmart_client.configuration_read() == snapshot


async def test_control_read(
    tsmart_client: TSmartClient,
    snapshot: SnapshotAssertion,
) -> None:
    """Test retrieving status."""

    with patch(
        "aiotsmart.TSmartClient._request",
        return_value=b"\xf1\x00\x00\x00d\x00\x00\xe0\x01\x00\x01\x1b\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x009",
    ):
        assert await tsmart_client.control_read() == snapshot


async def test_control_read_no_response(
    tsmart_client: TSmartClient,
    snapshot: SnapshotAssertion,
) -> None:
    """Test retrieving no response from status."""

    with patch("aiotsmart.TSmartClient._request", return_value=None):
        with pytest.raises(TSmartNoResponseError):
            assert await tsmart_client.control_read() == snapshot


async def test_control_set(
    tsmart_client: TSmartClient,
) -> None:
    """Test setting control."""

    with patch("aiotsmart.TSmartClient._request", return_value=b"\xf2\x00\x00\xa7"):
        await tsmart_client.control_write(power=True, mode=Mode.MANUAL, setpoint=15)


async def test_control_set_no_response(
    tsmart_client: TSmartClient,
) -> None:
    """Test setting control."""

    with patch("aiotsmart.TSmartClient._request", return_value=None):
        with pytest.raises(TSmartNoResponseError):
            await tsmart_client.control_write(power=True, mode=Mode.MANUAL, setpoint=15)
