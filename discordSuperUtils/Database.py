import aiopg
import aiosqlite
from motor import motor_asyncio
import asyncio
import aiomysql
import sys

if sys.version_info >= (3, 8) and sys.platform.lower().startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def create_mysql(host, port, user, password, dbname):
    # Created this function to make sure the user has autocommit enabled.
    # we must make sure autocommit is enabled because manual commits are not working on aiomysql :)
    return await aiomysql.create_pool(host=host, port=port, user=user, password=password, db=dbname, autocommit=True)


class UnsupportedDatabase(Exception):
    """Raises error when the user tries to use an unsupported database."""


class _MongoDatabase:
    def __init__(self, database):
        self.database = database

    def __str__(self):
        return f"<{self.__class__.__name__} '{self.name}'>"

    @property
    def name(self):
        return self.database.name

    async def close(self):
        self.database.client.close()

    async def insertifnotexists(self, table_name, data, checks):
        response = await self.select(table_name, [], checks, True)

        if not response:
            return await self.insert(table_name, data)

    async def insert(self, table_name, data):
        return await self.database[table_name].insert_one(data)

    async def create_table(self, table_name, columns=None, exists=False):
        if exists and table_name in await self.database.list_collection_names():
            return

        return await self.database.create_collection(table_name)

    async def update(self, table_name, data, checks):
        return await self.database[table_name].update_one(checks, {"$set": data})

    async def updateorinsert(self, table_name, data, checks, insert_data):
        response = await self.select(table_name, [], checks, True)

        if len(response) == 1:
            return await self.update(table_name, data, checks)

        return await self.insert(table_name, insert_data)

    async def delete(self, table_name, checks=None):
        return await self.database[table_name].delete_one({} if checks is None else checks)

    async def select(self, table_name, keys, checks=None, fetchall=False):
        checks = {} if checks is None else checks

        if fetchall:
            fetch = self.database[table_name].find(checks)
            result = []

            async for doc in fetch:
                current_doc = {}

                for key, value in doc.items():
                    if not keys or key in keys:
                        current_doc[key] = value

                result.append(current_doc)
        else:
            fetch = await self.database[table_name].find_one(checks)
            result = {}

            if fetch is not None:
                for key, value in fetch.items():
                    if not keys or key in keys:
                        result[key] = value
            else:
                result = None

        return result


class _SqlDatabase:
    def __str__(self):
        return f"<{self.__class__.__name__}>"

    def with_commit(func):
        async def inner(self, *args, **kwargs):
            resp = await func(self, *args, **kwargs)
            if self.commit_needed:
                await self.commit()

            return resp

        return inner

    def with_cursor(func):
        async def inner(self, *args, **kwargs):
            database = await self.database.acquire() if self.pool else self.database

            if self.cursor_context:
                async with database.cursor() as cursor:
                    resp = await func(self, cursor, *args, **kwargs)

            else:
                cursor = await database.cursor()
                resp = await func(self, cursor, *args, **kwargs)
                await cursor.close()

            if self.pool:
                self.database.release(database)

            return resp

        return inner

    def __init__(self, database):
        self.database = database
        self.place_holder = DATABASE_TYPES[type(database)]["placeholder"]
        self.cursor_context = DATABASE_TYPES[type(database)]['cursorcontext']
        self.commit_needed = DATABASE_TYPES[type(database)]['commit']
        self.quote = DATABASE_TYPES[type(database)]['quotes']
        self.pool = DATABASE_TYPES[type(database)]['pool']

    async def commit(self):
        if not self.pool:
            await self.database.commit()

    async def close(self):
        await self.database.close()

    async def insertifnotexists(self, table_name, data, checks):
        response = await self.select(table_name, [], checks, True)

        if not response:
            return await self.insert(table_name, data)

    @with_cursor
    @with_commit
    async def insert(self, cursor, table_name, data):
        query = f"INSERT INTO {table_name} ({', '.join(data.keys())}) VALUES ({', '.join([self.place_holder] * len(data.values()))})"
        await cursor.execute(query, list(data.values()))

    @with_cursor
    @with_commit
    async def create_table(self, cursor, table_name, columns=None, exists=False):
        query = f'CREATE TABLE {"IF NOT EXISTS" if exists else ""} {self.quote}{table_name}{self.quote} ('

        for column in [] if columns is None else columns:
            query += f"\n{self.quote}{column}{self.quote} {columns[column]},"
        query = query[:-1]

        query += "\n);"
        await cursor.execute(query)

    @with_cursor
    @with_commit
    async def update(self, cursor, table_name, data, checks):
        query = f"UPDATE {table_name} SET "

        if data:
            for key in data:
                query += f"{key} = {self.place_holder}, "
            query = query[:-2]

        if checks:
            query += " WHERE "
            for check in checks:
                query += f"{check} = {self.place_holder} AND "

            query = query[:-4]

        await cursor.execute(query, list(data.values()) + list(checks.values()))

    async def updateorinsert(self, table_name, data, checks, insert_data):
        response = await self.select(table_name, [], checks, True)

        if len(response) == 1:
            return await self.update(table_name, data, checks)

        return await self.insert(table_name, insert_data)

    @with_cursor
    @with_commit
    async def delete(self, cursor, table_name, checks=None):
        checks = {} if checks is None else checks

        query = f"DELETE FROM {table_name} "

        if checks:
            query += "WHERE "
            for check in checks:
                query += f"{list(check)[0]} = {self.place_holder} AND "

            query = query[:-4]

        values = [list(x.values())[0] for x in checks]
        await cursor.execute(query, values)

    @with_cursor
    async def select(self, cursor, table_name, keys, checks=None, fetchall=False):
        checks = {} if checks is None else checks

        keys = '*' if not keys else keys
        query = f"SELECT {','.join(keys)} FROM {table_name} "

        if checks:
            query += "WHERE "
            for check in checks:
                query += f"{check} = {self.place_holder} AND "

            query = query[:-4]

        await cursor.execute(query, list(checks.values()))
        columns = [x[0] for x in cursor.description]

        result = await cursor.fetchall() if fetchall else await cursor.fetchone()
        if not result:
            return result

        return [dict(zip(columns, x)) for x in result] if fetchall else dict(zip(columns, result))


DATABASE_TYPES = {
    motor_asyncio.AsyncIOMotorDatabase: {"class": _MongoDatabase, "placeholder": None},
    aiosqlite.core.Connection: {"class": _SqlDatabase, "placeholder": '?', 'cursorcontext': True, 'commit': True,
                                'quotes': '"', 'pool': False},
    aiopg.pool.Pool: {"class": _SqlDatabase, "placeholder": '%s', 'cursorcontext': True, 'commit': True, 'quotes': '"',
                      'pool': True},
    aiomysql.pool.Pool: {"class": _SqlDatabase, "placeholder": '%s', 'cursorcontext': True, 'commit': False,
                         'quotes': '`', 'pool': True}
}


class DatabaseManager:
    """
    A database class for easier access
    database MUST be of type sqlite3, mongodb or postgresql
    """

    @staticmethod
    def connect(database):
        if type(database) not in DATABASE_TYPES:
            raise UnsupportedDatabase(f"Database of type {type(database)} is not supported by the database manager.")

        return DATABASE_TYPES[type(database)]["class"](database)
