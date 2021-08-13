import asyncio
import sqlite3

import psycopg2.extensions
import pymongo.database

DATABASE_TYPES = {
    pymongo.database.Database: None,  # mongo does not require any columns
    sqlite3.Connection: {"snowflake": "INTEGER", "string": 'TEXT', "number": "INTEGER", "smallnumber": "INTEGER"},
    psycopg2.extensions.connection: {"snowflake": "bigint", "string": 'character varying', "number": "integer", "smallnumber": "smallint"}
}


def generate_column_types(types, database_type):
    database_type_configuration = DATABASE_TYPES.get(database_type)

    if database_type_configuration is None:
        return

    return [database_type_configuration[x] for x in types]


class EventManager:
    def __init__(self):
        self.events = {}

    async def call_event(self, name, *args, **kwargs):
        if name in self.events:
            for event in self.events[name]:
                await event(*args, **kwargs)

    def event(self, name=None):
        def inner(func):
            self.add_event(func, name)
            return func

        return inner

    def add_event(self, func, name=None):
        name = func.__name__ if not name else name

        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Listeners must be async.')

        if name in self.events:
            self.events[name].append(func)
        else:
            self.events[name] = [func]

    def remove_event(self, func, name=None):
        name = func.__name__ if not name else name

        if name in self.events:
            self.events[name].remove(func)