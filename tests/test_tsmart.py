"""Asynchronous Python client for TSmart."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import aiohttp
from aiohttp.hdrs import METH_POST
from aioresponses import CallbackResult, aioresponses
import pytest
from yarl import URL

from aiotsmart.exceptions import (
    TSmartAuthenticationError,
    TSmartConnectionError,
    TSmartError,
)
from aiotsmart.tsmart import TSmartClient
from tests import load_fixture

from .const import ANDREWS_ARNOLD_URL, HEADERS

if TYPE_CHECKING:
    from syrupy import SnapshotAssertion


async def test_authentication_error(
    responses: aioresponses,
    client: TSmartClient,
    snapshot: SnapshotAssertion,
) -> None:
    """Test retrieving info but not authorized."""

    url = URL(ANDREWS_ARNOLD_URL).joinpath("broadband/info")
    responses.post(
        url,
        status=200,
        body=load_fixture("authentication_error.json"),
    )

    with pytest.raises(TSmartAuthenticationError):
        assert await client.get_info() == snapshot


async def test_putting_in_own_session(
    responses: aioresponses,
) -> None:
    """Test putting in own session."""
    responses.post(
        f"{ANDREWS_ARNOLD_URL}/broadband/info",
        status=200,
        body=load_fixture("broadband_info.json"),
    )
    async with aiohttp.ClientSession() as session:
        client = TSmartClient(session=session)
        await client.get_info()
        assert client.session is not None
        assert not client.session.closed
        await client.close()
        assert not client.session.closed


async def test_creating_own_session(
    responses: aioresponses,
) -> None:
    """Test creating own session."""
    responses.post(
        f"{ANDREWS_ARNOLD_URL}/broadband/info",
        status=200,
        body=load_fixture("broadband_info.json"),
    )
    client = TSmartClient(control_login="XXX", control_password="XXX")
    await client.get_info()
    assert client.session is not None
    assert not client.session.closed
    await client.close()
    assert client.session.closed


async def test_unexpected_server_response(
    responses: aioresponses,
    client: TSmartClient,
) -> None:
    """Test handling unexpected response."""
    responses.post(
        f"{ANDREWS_ARNOLD_URL}/broadband/info",
        status=200,
        headers={"Content-Type": "plain/text"},
        body="Yes",
    )
    with pytest.raises(TSmartError):
        assert await client.get_info()


async def test_timeout(
    responses: aioresponses,
) -> None:
    """Test request timeout."""

    # Faking a timeout by sleeping
    async def response_handler(_: str, **_kwargs: Any) -> CallbackResult:
        """Response handler for this test."""
        await asyncio.sleep(2)
        return CallbackResult(body="Goodmorning!")

    url = URL(ANDREWS_ARNOLD_URL).joinpath("broadband/info")
    responses.post(
        url,
        callback=response_handler,
    )
    async with TSmartClient(request_timeout=1) as client:
        with pytest.raises(TSmartConnectionError):
            assert await client.get_info()


async def test_info(
    responses: aioresponses,
    client: TSmartClient,
    snapshot: SnapshotAssertion,
) -> None:
    """Test retrieving info."""

    url = URL(ANDREWS_ARNOLD_URL).joinpath("broadband/info")
    responses.post(
        url,
        status=200,
        body=load_fixture("broadband_info.json"),
    )
    assert await client.get_info() == snapshot

    responses.assert_called_once_with(
        f"{ANDREWS_ARNOLD_URL}/broadband/info",
        METH_POST,
        headers=HEADERS,
        params=None,
        json={"control_login": "test", "control_password": "test"},
    )
