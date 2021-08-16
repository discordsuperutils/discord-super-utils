import aiopg

import discordSuperUtils
import aiosqlite
from motor import motor_asyncio
import asyncio


async def database_test():
    mongo_database = discordSuperUtils.DatabaseManager.connect(motor_asyncio.AsyncIOMotorClient("con-string")['name'])
    # Replace 'con-string' with the MongoDB connection string and 'name' by the database name you want to use.

    postgre_database = discordSuperUtils.DatabaseManager.connect(await aiopg.create_pool("con-string"))
    # Replace 'con-string' with the PostrgeSQL connection string.
    # PostgreSQL connection string example:
    # "dbname=name user=postgres password=xxx host=host" host is not required.

    mysql_database = await discordSuperUtils.create_mysql(host=..., port=..., user=..., password=..., dbname=...)
    # Replace '...' with the arguments.
    # create_mysql supports mysql AND mariaDB

    sqlite_database = discordSuperUtils.DatabaseManager.connect(await aiosqlite.connect('path'))
    # Replace 'path' with the SQLite database path. (must be on your computer)

    await sqlite_database.insert('economy', {'guild': ..., 'member': ..., 'currency': ..., 'bank': ...})

    await sqlite_database.close()  # not required.


loop = asyncio.get_event_loop()
loop.run_until_complete(database_test())
