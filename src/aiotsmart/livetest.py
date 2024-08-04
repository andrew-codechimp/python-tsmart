"""Tests."""

from pprint import pprint
import asyncio
from aiotsmart.tsmart import TSmart


client = TSmart("192.168.1.35")


async def do_stuff():
    """Test."""
    # configuration = await client.async_get_configuration()
    # pprint(vars(configuration))

    status = await client.async_get_status()
    pprint(vars(status))

    pprint(vars(client))


asyncio.run(do_stuff())
