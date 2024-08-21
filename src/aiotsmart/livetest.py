"""Tests."""

import asyncio

from aiotsmart import TSmartClient, Mode


client = TSmartClient("192.168.1.35")


async def do_stuff():
    """Test."""

    # discovery = TSmartDiscovery()
    # devices = await discovery.discover()
    # print(devices)

    # configuration = await client.configuration_read()
    # print(configuration)

    status = await client.control_read()
    print(status)

    print(status.has_error)

    # try:
    #     status = await client.control_read()
    #     pprint(vars(status))
    # except TSmartError as exception:
    #     print(repr(exception))

    # await client.control_write(power=True, mode=Mode.MANUAL, setpoint=15)

    # pprint(vars(client))


asyncio.run(do_stuff())
