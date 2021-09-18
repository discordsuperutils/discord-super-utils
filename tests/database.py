import asyncio

import discordSuperUtils.Base
from tester import Tester


async def get_database():
    return discordSuperUtils.DatabaseManager.connect(...)


async def start_testing():
    tester = Tester(
        gather=False
    )  # Database tester should not use gather mode because if it does the tests don't work
    tester.add_test(check_table_and_delete, [], ())
    tester.add_test(check_insert, [{"id": 1}])
    tester.add_test(check_update, [{"id": 2}])
    tester.add_test(check_execute, [{"id": 1}], ignored_exception=NotImplementedError)
    await tester.run()


def remove_id(search):
    for result in search:
        if "_id" in result:
            del result["_id"]


async def check_table_and_delete():
    types = discordSuperUtils.Base.generate_column_types(
        ["number"], type(database.database)
    )

    await database.create_table(
        "database_testing", dict(zip(["id"], types)) if types else None, True
    )
    await database.delete("database_testing")

    return await database.select("database_testing", [], fetchall=True)


async def check_insert():
    await check_table_and_delete()

    await database.insert("database_testing", {"id": 1})
    select = await database.select("database_testing", [], fetchall=True)

    remove_id(select)
    return select


async def check_update():
    await check_table_and_delete()

    await database.insert("database_testing", {"id": 1})
    await database.update("database_testing", {"id": 2}, {"id": 1})
    select = await database.select("database_testing", [], fetchall=True)

    remove_id(select)
    return select


async def check_execute():
    await check_table_and_delete()

    await database.insert("database_testing", {"id": 1})
    select = await database.execute(
        "SELECT * FROM database_testing WHERE id = 1", fetchall=True
    )

    remove_id(select)
    return select


loop = asyncio.get_event_loop()
database = loop.run_until_complete(get_database())
loop.run_until_complete(start_testing())
