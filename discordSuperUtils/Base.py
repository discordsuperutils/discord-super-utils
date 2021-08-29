import asyncio
import inspect
from typing import List

import aiomysql
import aiopg
import aiosqlite
import discord
from motor import motor_asyncio

COLUMN_TYPES = {
    motor_asyncio.AsyncIOMotorDatabase: None,  # mongo does not require any columns
    aiosqlite.core.Connection: {"snowflake": "INTEGER", "string": 'TEXT', "number": "INTEGER", "smallnumber": "INTEGER"},
    aiopg.pool.Pool: {"snowflake": "bigint", "string": 'character varying', "number": "integer", "smallnumber": "smallint"},
    aiomysql.pool.Pool: {"snowflake": "BIGINT", "string": 'TEXT', "number": "INT", "smallnumber": "SMALLINT"}
}


class DatabaseNotConnected(Exception):
    """Raises an error when the user tries to use a method of a manager without a database connected to it."""


def generate_column_types(types, database_type):
    database_type_configuration = COLUMN_TYPES.get(database_type)

    if database_type_configuration is None:
        return

    return [database_type_configuration[x] for x in types]


async def questionnaire(ctx, questions, public=False, timeout=30, member=None):
    answers = []
    timed_out = False

    if not public and not member:
        raise ValueError("The questionnaire is private and no member was provided.")

    def checks(msg):
        return msg.channel == ctx.channel if public else msg.channel == ctx.channel and msg.author == member

    for question in questions:
        if isinstance(question, str):
            await ctx.send(question)
        elif isinstance(question, discord.Embed):
            await ctx.send(embed=question)
        else:
            raise TypeError("Question must be of type 'str' or 'discord.Embed'.")

        try:
            message = await ctx.bot.wait_for('message', check=checks, timeout=timeout)
        except asyncio.TimeoutError:
            timed_out = True
            break

        answers.append(message.content)

    return answers, timed_out


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


class CogManager:
    class Cog:
        def __init__(self, managers: List = None):
            listeners = {}
            managers = [] if managers is None else managers

            attribute_objects = [getattr(self, attr) for attr in dir(self)]

            for attr in attribute_objects:
                listener_type = getattr(attr, "_listener_type", None)
                if listener_type:
                    if listener_type in listeners:
                        listeners[listener_type].append(attr)
                    else:
                        listeners[listener_type] = [attr]

            if not managers:
                for attr in attribute_objects:
                    if type(attr) in listeners:
                        managers.append(attr)

            for event_type in listeners:
                for manager in managers:
                    if isinstance(manager, event_type):
                        for event in listeners[event_type]:
                            manager.add_event(event)

    @staticmethod
    def event(manager_type):
        def decorator(func):
            if not inspect.iscoroutinefunction(func):
                raise TypeError('Listeners must be async.')

            func._listener_type = manager_type

            return func

        return decorator


class DatabaseChecker(EventManager):
    def __init__(self, column_names, column_types):
        super().__init__()

        self.database = None
        self.table = None
        self.column_names = column_names
        self.column_types = column_types

    def _check_database(self, raise_error=True):
        if not self.database:
            if raise_error:
                raise DatabaseNotConnected(f"Database not connected."
                                           f" Connect this manager to a database using 'connect_to_database'")

            return False

        return True

    async def connect_to_database(self, database, table):
        types = generate_column_types(self.column_types,
                                      type(database.database))

        await database.create_table(table, dict(zip(self.column_names, types)) if types else None, True)

        self.database = database
        self.table = table

        await self.call_event("on_database_connect")
