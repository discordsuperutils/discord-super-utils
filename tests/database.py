import discordSuperUtils.Base

from tester import Tester
import asyncio


async def get_database():
    return discordSuperUtils.DatabaseManager.connect(...)


async def start_testing():
    tester = Tester()
    tester.add_test(check_table_and_delete, [], ())
    tester.add_test(check_insert, [{"id": 1}])
    tester.add_test(check_update, [{"id": 2}])
    await tester.run()


def remove_id(search):
    for result in search:
        if "_id" in result:
            del result["_id"]


async def check_table_and_delete():
    types = discordSuperUtils.Base.generate_column_types(['number'], type(database.database))

    await database.create_table("database_testing", dict(zip(['id'], types)) if types else None, True)
    await database.delete("database_testing")

    return await database.select("database_testing", [], fetchall=True)


async def check_insert():
    await check_table_and_delete()

    await database.insert("database_testing", {'id': 1})
    select = await database.select("database_testing", [], fetchall=True)

    remove_id(select)
    return select


async def check_update():
    await check_table_and_delete()

    await database.insert("database_testing", {'id': 1})
    await database.update("database_testing", {"id": 2}, {"id": 1})
    select = await database.select("database_testing", [], fetchall=True)

    remove_id(select)
    return select


loop = asyncio.get_event_loop()
database = loop.run_until_complete(get_database())
loop.run_until_complete(start_testing())