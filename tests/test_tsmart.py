"""Asynchronous Python client for TSmart."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from yarl import URL

from aiotsmart.exceptions import TSmartConnectionError, TSmartError
from aiotsmart.tsmart import TSmart

from .const import IP_ADDRESS

if TYPE_CHECKING:
    from syrupy import SnapshotAssertion


async def test_get_configuration(
    snapshot: SnapshotAssertion,
):
    """Test retrieving configuration."""

    client = TSmart(ip=IP_ADDRESS)

    with patch(
        "aiotsmart.TSmart._async_request",
        return_value=b"!\x00\x00 \x00\r*\x9b\x00TESLA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00d\x00\x01\t`Boiler\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\xff\xff\x01\x01\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\xff\xff\xff\xff\x00\x00wifissid\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00wifipassword\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd0!\xf9\xb1\xd6QTESLA_74BA1D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0c\x01\xa7\x1e\x00\x00\x00\x00\x00\x04d\x00\t\x00\x00\x00\x01\x00\x00\x00n",
    ):
        assert await client.async_get_configuration() == snapshot


async def test_get_status(
    snapshot: SnapshotAssertion,
):
    """Test retrieving status."""

    client = TSmart(ip=IP_ADDRESS)

    with patch(
        "aiotsmart.TSmart._async_request",
        return_value=b"\xf1\x00\x00\x00d\x00\x00\xe0\x01\x00\x01\x1b\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x009",
    ):
        assert await client.async_get_status() == snapshot


# async def test_authentication_error(
#     responses: aioresponses,
#     client: TSmart,
#     snapshot: SnapshotAssertion,
# ) -> None:
#     """Test retrieving info but not authorized."""

#     url = URL(ANDREWS_ARNOLD_URL).joinpath("broadband/info")

#     responses.post(
#         url,
#         status=200,
#         body=load_fixture("authentication_error.json"),
#     )

#     with pytest.raises(TSmartAuthenticationError):
#         assert await client.get_info() == snapshot


# async def test_putting_in_own_session(
#     responses: aioresponses,
# ) -> None:
#     """Test putting in own session."""
#     responses.post(
#         f"{ANDREWS_ARNOLD_URL}/broadband/info",
#         status=200,
#         body=load_fixture("broadband_info.json"),
#     )
#     async with aiohttp.ClientSession() as session:
#         client = TSmart(session=session)
#         await client.get_info()
#         assert client.session is not None
#         assert not client.session.closed
#         await client.close()
#         assert not client.session.closed


# async def test_creating_own_session(
#     responses: aioresponses,
# ) -> None:
#     """Test creating own session."""
#     responses.post(
#         f"{ANDREWS_ARNOLD_URL}/broadband/info",
#         status=200,
#         body=load_fixture("broadband_info.json"),
#     )
#     client = TSmart(ip="172.0.0.1")
#     await client.get_info()
#     assert client.session is not None
#     assert not client.session.closed
#     await client.close()
#     assert client.session.closed


# async def test_unexpected_server_response(
#     responses: aioresponses,
#     client: TSmart,
# ) -> None:
#     """Test handling unexpected response."""
#     responses.post(
#         f"{ANDREWS_ARNOLD_URL}/broadband/info",
#         status=200,
#         headers={"Content-Type": "plain/text"},
#         body="Yes",
#     )
#     with pytest.raises(TSmartError):
#         assert await client.get_info()


# async def test_timeout(
#     responses: aioresponses,
# ) -> None:
#     """Test request timeout."""

#     # Faking a timeout by sleeping
#     async def response_handler(_: str, **_kwargs: Any) -> CallbackResult:
#         """Response handler for this test."""
#         await asyncio.sleep(2)
#         return CallbackResult(body="Goodmorning!")

#     url = URL(ANDREWS_ARNOLD_URL).joinpath("broadband/info")
#     responses.post(
#         url,
#         callback=response_handler,
#     )
#     async with TSmart(request_timeout=1) as client:
#         with pytest.raises(TSmartConnectionError):
#             assert await client.get_info()


# async def test_info(
#     responses: aioresponses,
#     client: TSmart,
#     snapshot: SnapshotAssertion,
# ) -> None:
#     """Test retrieving info."""

#     url = URL(ANDREWS_ARNOLD_URL).joinpath("broadband/info")
#     responses.post(
#         url,
#         status=200,
#         body=load_fixture("broadband_info.json"),
#     )
#     assert await client.get_info() == snapshot

#     responses.assert_called_once_with(
#         f"{ANDREWS_ARNOLD_URL}/broadband/info",
#         METH_POST,
#         headers=HEADERS,
#         params=None,
#         json={"control_login": "test", "control_password": "test"},
#     )
