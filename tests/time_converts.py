import asyncio

from discord.ext.commands import BadArgument

import discordSuperUtils
from tester import Tester


async def start_testing():
    """
    RESULTS
    --------
        convert_float: 1.5m: Passed 0.0ms
        convert_perm: perm: Passed 0.0ms
        convert_valid: 7d: Passed 0.0ms
        convert_valid2: 1m: Passed 0.0ms
        convert_invalid: heyh: Passed 0.0ms raised BadArgument
        convert_invalid: 100j: Passed 0.0ms raised BadArgument

    Conclusion
    ----------
        Everything seems to work perfectly.
    """

    tester = Tester()
    tester.add_test(convert_valid, 604800)
    tester.add_test(convert_valid2, 60)
    tester.add_test(convert_perm, 0)
    tester.add_test(convert_float, 90)
    tester.add_test(convert_invalid, None, ignored_exception=BadArgument)
    tester.add_test(convert_invalid2, None, ignored_exception=BadArgument)
    await tester.run()


async def convert_valid():
    return await convertor.convert(None, "7d")


async def convert_valid2():
    return await convertor.convert(None, "1m")


async def convert_float():
    return await convertor.convert(None, "1.5m")


async def convert_perm():
    return await convertor.convert(None, "perm")


async def convert_invalid():
    return await convertor.convert(None, "heyh")


async def convert_invalid2():
    return await convertor.convert(None, "100j")


convertor = discordSuperUtils.TimeConvertor()
asyncio.run(start_testing())
