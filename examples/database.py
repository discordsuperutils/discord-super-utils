import discordSuperUtils
import aiosqlite
from motor import motor_asyncio
import asyncio


async def database_test():
    mongo_database = discordSuperUtils.DatabaseManager.connect(motor_asyncio.AsyncIOMotorClient("con-string")['name'])
    # Replace 'con-string' by the MongoDB connection string and 'name' by the database name you want to use.

    postgre_database = discordSuperUtils.DatabaseManager.connect(await discordSuperUtils.create_postgre("con-string"))
    # Replace 'con-string' by the PostrgeSQL connection string.
    # PostgreSQL connection string example:
    # "dbname=name user=postgres password=xxx host=host" host is not required.

    sqlite_database = discordSuperUtils.DatabaseManager.connect(await aiosqlite.connect('path'))
    # Replace 'path' by the SQLite database path. (must be on your computer)

    await sqlite_database.insert('economy', {'guild': ..., 'member': ..., 'currency': ..., 'bank': ...})

    await sqlite_database.close()  # not required.


loop = asyncio.get_event_loop()
loop.run_until_complete(database_test())