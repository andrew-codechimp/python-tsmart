"""Asynchronous Python client for TSmart."""

from typing import AsyncGenerator, Generator

import aiohttp
from aioresponses import aioresponses
import pytest

from aiotsmart import TSmartClient
from syrupy import SnapshotAssertion

from .syrupy import TSmartSnapshotExtension


@pytest.fixture(name="snapshot")
def snapshot_assertion(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the TSmart extension."""
    return snapshot.use_extension(TSmartSnapshotExtension)


@pytest.fixture(name="client")
async def client() -> AsyncGenerator[TSmartClient, None]:
    """Return a TSmart client."""
    async with aiohttp.ClientSession() as session, TSmartClient(
        control_login="test",
        control_password="test",
        session=session,
    ) as tsmart_client:
        yield tsmart_client


@pytest.fixture(name="responses")
def aioresponses_fixture() -> Generator[aioresponses, None, None]:
    """Return aioresponses fixture."""
    with aioresponses() as mocked_responses:
        yield mocked_responses
