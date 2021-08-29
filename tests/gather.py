import asyncio

from tester import Tester


async def start_testing():
    tester = Tester()
    tester.add_test(do_task, None)
    tester.add_test(do_multiple_task, None)
    tester.add_test(fancy_do_multiple_task, None)
    await tester.run()


async def do_task():
    await asyncio.sleep(1)  # do fancy stuff


async def do_multiple_task():
    for i in range(10):
        await do_task()


async def fancy_do_multiple_task():
    await asyncio.gather(*[do_task() for i in range(10)])


asyncio.run(start_testing())