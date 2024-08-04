"""Tests."""

from pprint import pprint
import asyncio
from aiotsmart.tsmart import TSmart


client = TSmart("192.168.1.35")


async def get_configuration():
    """Test the configuration."""
    await client.async_get_configuration()

    pprint(vars(client))


asyncio.run(get_configuration())
