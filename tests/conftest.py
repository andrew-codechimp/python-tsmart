"""Asynchronous Python client for TSmart."""

from typing import AsyncGenerator

import pytest

from aiotsmart import TSmartClient, TSmartDiscovery
from syrupy import SnapshotAssertion

from .syrupy import TSmartSnapshotExtension


@pytest.fixture(name="snapshot")
def snapshot_assertion(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the TSmart extension."""
    return snapshot.use_extension(TSmartSnapshotExtension)


@pytest.fixture(name="tsmart_client")
async def client() -> AsyncGenerator[TSmartClient, None]:
    """Return a TSmart client."""
    async with TSmartClient("127.0.0.1") as tsmart_client:
        yield tsmart_client


@pytest.fixture(name="tsmart_discovery")
async def discovery() -> AsyncGenerator[TSmartDiscovery, None]:
    """Return a TSmart client."""
    async with TSmartDiscovery() as tsmart_discovery:
        yield tsmart_discovery
