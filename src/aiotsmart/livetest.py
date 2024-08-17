"""Tests."""

import asyncio
from aiotsmart.tsmart import TSmartClient
from aiotsmart.discovery import TSmartDiscovery


# client = TSmartClient()
client = TSmartClient("192.168.1.35")
discovery = TSmartDiscovery()


async def do_stuff():
    """Test."""

    # devices = await discovery.discover()

    # print(devices)

    configuration = await client.configuration_read()
    print(configuration)
    print(vars(configuration))

    # try:
    #     status = await client.control_read()
    #     pprint(vars(status))
    # except TSmartConnectionError as exception:
    #     print(repr(exception))

    # await client.control_write(power=True, mode=Mode.MANUAL, setpoint=15)

    # pprint(vars(client))


asyncio.run(do_stuff())
