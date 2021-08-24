import discordSuperUtils
import asyncio


async def fivem_test():
    fivem_server = await discordSuperUtils.FiveMServer.fetch(...)  # Replace ... by the IP (port is needed!)
    # e.g. localhost:30120

    print(fivem_server.players)


asyncio.run(fivem_test())
