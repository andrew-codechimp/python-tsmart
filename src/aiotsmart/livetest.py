"""Tests."""

from pprint import pprint
import asyncio
from aiotsmart.tsmart import TSmart, Mode, TSmartConnectionError


client = TSmart("192.168.1.35")


async def do_stuff():
    """Test."""

    configuration = await client.async_get_configuration()
    pprint(vars(configuration))

    # try:
    #     status = await client.async_get_status()
    #     pprint(vars(status))
    # except TSmartConnectionError as exception:
    #     print(repr(exception))

    # await client.async_control_set(power=True, mode=Mode.MANUAL, setpoint=15)

    pprint(vars(client))


asyncio.run(do_stuff())
