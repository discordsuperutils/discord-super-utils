import asyncio
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union

import aiomysql

try:
    import aiopg
except ImportError:
    aiopg = None

import aiosqlite
from motor import motor_asyncio

if sys.version_info >= (3, 8) and sys.platform.lower().startswith("win"):
    # Aiopg requires the event loop policy to be WindowsSelectorEventLoop, if it is not, aiopg raises an error.

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def create_mysql(
    host: str, port: int, user: str, password: str, dbname: str
) -> aiomysql.pool.Pool:
    """
    |coro|

    Returns a mysql connection pool.

    :param str host: The host address.
    :param int port: The port.
    :param str user: The user.
    :param str password: The password.
    :param str dbname: The dbname.
    :return: The pool
    :rtype: aiomysql.pool.Pool
    """

    # Created this function to make sure the user has autocommit enabled.
    # we must make sure autocommit is enabled because manual commits are not working on aiomysql :)
    return await aiomysql.create_pool(
        host=host, port=port, user=user, password=password, db=dbname, autocommit=True
    )


class UnsupportedDatabase(Exception):
    """Raises error when the user tries to use an unsupported database."""


class Database(ABC):
    __slots__ = ("database",)

    def __init__(self, database):
        self.database = database

    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    async def insertifnotexists(
        self, table_name: str, data: Dict[str, Any], checks: Dict[str, Any]
    ):
        pass

    @abstractmethod
    async def insert(self, table_name: str, data: Dict[str, Any]):
        pass

    @abstractmethod
    async def create_table(
        self,
        table_name: str,
        columns: Optional[Dict[str, str]] = None,
        exists: Optional[bool] = False,
    ):
        pass

    @abstractmethod
    async def update(
        self, table_name: str, data: Dict[str, Any], checks: Dict[str, Any]
    ):
        pass

    @abstractmethod
    async def updateorinsert(
        self,
        table_name: str,
        data: Dict[str, Any],
        checks: Dict[str, Any],
        insert_data: Dict[str, Any],
    ):
        pass

    @abstractmethod
    async def delete(self, table_name: str, checks: Dict[str, Any]):
        pass

    @abstractmethod
    async def select(
        self,
        table_name: str,
        keys: List[str],
        checks: Optional[Dict[str, Any]] = None,
        fetchall: Optional[bool] = False,
    ):
        pass

    @abstractmethod
    async def execute(
        self, sql_query: str, values: List[Any], fetchall: bool = True
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        pass


class _MongoDatabase(Database):
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

    async def create_table(self, table_name, _=None, exists=False):
        # create_table has an unused positional parameter to make the methods consistent between database types.

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
        return await self.database[table_name].delete_one(
            {} if checks is None else checks
        )

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

    async def execute(
        self, sql_query: str, values: List[Any], fetchall: bool = True
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        raise NotImplementedError("NoSQL databases cannot execute sql queries.")


class _SqlDatabase(Database):
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
        super().__init__(database)
        self.place_holder = DATABASE_TYPES[type(database)]["placeholder"]
        self.cursor_context = DATABASE_TYPES[type(database)]["cursorcontext"]
        self.commit_needed = DATABASE_TYPES[type(database)]["commit"]
        self.quote = DATABASE_TYPES[type(database)]["quotes"]
        self.pool = DATABASE_TYPES[type(database)]["pool"]

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
        columns = [] if columns is None else columns

        for column in columns:
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
                query += f"{check} = {self.place_holder} AND "

            query = query[:-4]

        await cursor.execute(query, list(checks.values()))

    @with_cursor
    async def select(self, cursor, table_name, keys, checks=None, fetchall=False):
        checks = {} if checks is None else checks

        keys = "*" if not keys else keys
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

        return (
            [dict(zip(columns, x)) for x in result]
            if fetchall
            else dict(zip(columns, result))
        )

    @with_cursor
    @with_commit
    async def execute(
        self, cursor, sql_query: str, values: List[Any] = None, fetchall: bool = True
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        await cursor.execute(sql_query, values if values is not None else [])

        result = await cursor.fetchall() if fetchall else await cursor.fetchone()
        columns = [x[0] for x in cursor.description]
        if not result:
            return result

        return (
            [dict(zip(columns, x)) for x in result]
            if fetchall
            else dict(zip(columns, result))
        )


DATABASE_TYPES: Dict[Any, Dict[str, Any]] = {
    motor_asyncio.AsyncIOMotorDatabase: {"class": _MongoDatabase, "placeholder": None},
    aiosqlite.core.Connection: {
        "class": _SqlDatabase,
        "placeholder": "?",
        "cursorcontext": True,
        "commit": True,
        "quotes": '"',
        "pool": False,
    },
    aiomysql.pool.Pool: {
        "class": _SqlDatabase,
        "placeholder": "%s",
        "cursorcontext": True,
        "commit": False,
        "quotes": "`",
        "pool": True,
    },
}

if aiopg:
    DATABASE_TYPES[aiopg.pool.Pool] = {
        "class": _SqlDatabase,
        "placeholder": "%s",
        "cursorcontext": True,
        "commit": True,
        "quotes": '"',
        "pool": True,
    }

DATABASES: List = [_SqlDatabase, _MongoDatabase]


class DatabaseManager:
    """
    Represents a DatabaseManager.
    """

    @staticmethod
    def connect(database: Any) -> Optional[Database]:
        """
        Connects to a database.

        :param Any database: The database.
        :return: The database, if applicable.
        :rtype: Optional[Database]
        """

        if type(database) not in DATABASE_TYPES:
            raise UnsupportedDatabase(
                f"Database of type {type(database)} is not supported by the database manager."
            )

        return DATABASE_TYPES[type(database)]["class"](database)
