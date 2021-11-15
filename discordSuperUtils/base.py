from __future__ import annotations

import asyncio
import dataclasses
import inspect
import logging
from dataclasses import dataclass
from typing import (
    List,
    Any,
    Iterable,
    Optional,
    TYPE_CHECKING,
    Union,
    Tuple,
    Callable,
    Dict,
    Coroutine,
)

import aiomysql

try:
    import aiopg
except ImportError:
    aiopg = None
    logging.warning(
        "Aiopg is not installed correctly, postgres databases are not supported."
    )

import aiosqlite
import discord
from motor import motor_asyncio

if TYPE_CHECKING:
    from discord.ext import commands
    from .database import Database
    from datetime import timedelta


__all__ = (
    "COLUMN_TYPES",
    "DatabaseNotConnected",
    "InvalidGenerator",
    "get_generator_response",
    "maybe_coroutine",
    "generate_column_types",
    "questionnaire",
    "EventManager",
    "create_task",
    "CogManager",
    "DatabaseChecker",
    "CacheBased",
)


COLUMN_TYPES = {
    motor_asyncio.AsyncIOMotorDatabase: None,  # mongo does not require any columns
    aiosqlite.core.Connection: {
        "snowflake": "INTEGER",
        "string": "TEXT",
        "number": "INTEGER",
        "smallnumber": "INTEGER",
    },
    aiomysql.pool.Pool: {
        "snowflake": "BIGINT",
        "string": "TEXT",
        "number": "INT",
        "smallnumber": "SMALLINT",
    },
}

if aiopg:
    COLUMN_TYPES[aiopg.pool.Pool] = {
        "snowflake": "BIGINT",
        "string": "TEXT",
        "number": "INT",
        "smallnumber": "SMALLINT",
    }


class DatabaseNotConnected(Exception):
    """Raises an error when the user tries to use a method of a manager without a database connected to it."""


@dataclass
class CacheBased:
    """
    Represents a cache manager that manages member cache.
    """

    bot: commands.Bot
    wipe_cache_delay: timedelta
    _cache: dict = dataclasses.field(default_factory=dict, init=False, repr=False)

    def __post_init__(self):
        asyncio.get_event_loop().create_task(self.__wipe_cache())

    async def __wipe_cache(self) -> None:
        """
        |coro|

        This function is responsible for wiping the member cache.

        :return: None
        :rtype: None
        """

        while not self.bot.is_closed():
            await asyncio.sleep(self.wipe_cache_delay.total_seconds())

            self._cache = {}


class InvalidGenerator(Exception):
    """
    Raises an exception when the user passes an invalid generator.
    """

    __slots__ = ("generator",)

    def __init__(self, generator):
        self.generator = generator
        super().__init__(
            f"Generator of type {type(self.generator)!r} is not supported."
        )


async def maybe_coroutine(function: Callable, *args, **kwargs) -> Any:
    """
    |coro|

    Returns the return value of the function.

    :param Callable function: The function to call.
    :param args: The arguments.
    :param kwargs: The key arguments:
    :return: The value.
    :rtype: Any
    """

    value = function(*args, **kwargs)

    if inspect.isawaitable(value):
        return await value

    return value


def get_generator_response(generator: Any, generator_type: Any, *args, **kwargs) -> Any:
    """
    Returns the generator response with the arguments.

    :param generator: The generator to get the response from.
    :type generator: Any
    :param generator_type: The generator type. (Should be same as the generator type.
    :type generator_type: Any
    :param args: The arguments of the generator.
    :param kwargs: The key arguments of the generator
    :return: The generator response.
    :rtype: Any
    """

    if inspect.isclass(generator) and issubclass(generator, generator_type):
        if inspect.ismethod(generator.generate):
            return generator.generate(*args, **kwargs)

        return generator().generate(*args, **kwargs)

    if isinstance(generator, generator_type):
        return generator.generate(*args, **kwargs)

    raise InvalidGenerator(generator)


def generate_column_types(
    types: Iterable[str], database_type: Any
) -> Optional[List[str]]:
    """
    Generates the column type names that are suitable for the database type.

    :param types: The column types.
    :type types: Iterable[str]
    :param database_type: The database type.
    :type database_type: Any
    :return: The suitable column types for the database types.
    :rtype: Optional[List[str]]
    """

    database_type_configuration = COLUMN_TYPES.get(database_type)

    if database_type_configuration is None:
        return

    return [database_type_configuration[x] for x in types]


async def questionnaire(
    ctx: commands.Context,
    questions: Iterable[Union[str, discord.Embed]],
    public: bool = False,
    timeout: Union[float, int] = 30,
    member: discord.Member = None,
) -> Tuple[List[str], bool]:
    """
    |coro|

    Questions the member using a "quiz" and returns the answers.
    The questionnaire can be used without a specific member and be public.
    If no member was passed and the questionnaire public argument is true, a ValueError will be raised.

    :raises: ValueError: The questionnaire is private and no member was provided.
    :param ctx: The context (where the questionnaire will ask the questions).
    :type ctx: commands.Context
    :param questions: The questions the questionnaire will ask.
    :type questions: Iterable[Union[str, discord.Embed]]
    :param public: A bool indicating if the questionnaire is public.
    :type public: bool
    :param timeout: The number of seconds until the questionnaire will stop and time out.
    :type timeout: Union[float, int]
    :param member: The member the questionnaire will get the answers from.
    :type member: discord.Member
    :return: The answers and a boolean indicating if the questionnaire timed out.
    :rtype: Tuple[List[str], bool]
    """

    answers = []
    timed_out = False

    if not public and not member:
        raise ValueError("The questionnaire is private and no member was provided.")

    def checks(msg):
        return (
            msg.channel == ctx.channel
            if public
            else msg.channel == ctx.channel and msg.author == member
        )

    for question in questions:
        if isinstance(question, str):
            await ctx.send(question)
        elif isinstance(question, discord.Embed):
            await ctx.send(embed=question)
        else:
            raise TypeError("Question must be of type 'str' or 'discord.Embed'.")

        try:
            message = await ctx.bot.wait_for("message", check=checks, timeout=timeout)
        except asyncio.TimeoutError:
            timed_out = True
            break

        answers.append(message.content)

    return answers, timed_out


@dataclass
class EventManager:
    """
    An event manager that manages events for managers.
    """

    events: dict = dataclasses.field(default_factory=dict, init=False)

    async def call_event(self, name: str, *args, **kwargs) -> None:
        """
        Calls the event name with the arguments

        :param name: The event name.
        :type name: str
        :param args: The arguments.
        :param kwargs: The key arguments.
        :return: None
        :rtype: None
        """

        if name in self.events:
            for event in self.events[name]:
                await event(*args, **kwargs)

    def event(self, name: str = None) -> Callable:
        """
        A decorator which adds an event listener.

        :param name: The event name.
        :type name: str
        :return: The inner function.
        :rtype: Callable
        """

        def inner(func):
            self.add_event(func, name)
            return func

        return inner

    def add_event(self, func: Callable, name: str = None) -> None:
        """
        Adds an event to the event dictionary.

        :param func: The event callback.
        :type func: Callable
        :param name: The event name.
        :type name: str
        :return: None
        :rtype: None
        :raises: TypeError: The listener isn't async.
        """

        name = func.__name__ if not name else name

        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Listeners must be async.")

        if name in self.events:
            self.events[name].append(func)
        else:
            self.events[name] = [func]

    def remove_event(self, func: Callable, name: str = None) -> None:
        """
        Removes an event from the event dictionary.

        :param func: The event callback.
        :type func: Callable
        :param name: The event name.
        :type name: str
        :return: None
        :rtype: None
        """

        name = func.__name__ if not name else name

        if name in self.events:
            self.events[name].remove(func)


def handle_task_exceptions(task: asyncio.Task) -> None:
    """
    Handles the task's exceptions.

    :param asyncio.Task task: The task.
    :return: None
    :rtype: None
    """

    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        raise e


def create_task(loop: asyncio.AbstractEventLoop, coroutine: Coroutine) -> None:
    """
    Creates a task and handles exceptions.

    :param asyncio.AbstractEventLoop loop: The loop to run the coroutine on.
    :param Coroutine coroutine: The coroutine.
    :return: None
    :rtype: None
    """

    try:
        task = loop.create_task(coroutine)
        task.add_done_callback(handle_task_exceptions)
    except RuntimeError:
        pass


class CogManager:
    """
    A CogManager which helps the user use the managers inside discord cogs.
    """

    class Cog:
        """
        The internal Cog class.
        """

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

            managers = managers or [
                attr for attr in attribute_objects if type(attr) in listeners
            ]
            for event_type in listeners:
                for manager in managers:
                    for event in listeners[event_type]:
                        manager.add_event(event)

    @staticmethod
    def event(manager_type: Any) -> Callable:
        """
        Adds an event to the Cog event list.

        :param manager_type: The manager type of the event.
        :type manager_type: Any
        :rtype: Callable
        :return: The inner function.
        :raises: TypeError: The listener isn't async.
        """

        def decorator(func):
            if not inspect.iscoroutinefunction(func):
                raise TypeError("Listeners must be async.")

            func._listener_type = manager_type

            return func

        return decorator


@dataclass
class DatabaseChecker(EventManager):
    """
    A database checker which makes sure the database is connected to a manager and handles the table creation.
    """

    tables_column_data: List[Dict[str, str]]
    table_identifiers: List[str]
    database: Optional[Database] = dataclasses.field(default=None, init=False)
    tables: Dict[str, str] = dataclasses.field(default_factory=dict, init=False)

    @staticmethod
    def uses_database(func):
        def inner(self, *args, **kwargs):
            self._check_database()
            return func(self, *args, **kwargs)

        return inner

    def _check_database(self, raise_error: bool = True) -> bool:
        """
        A function which checks if the database is connected.

        :param raise_error: A bool indicating if the function should raise an error if the database is not connected.
        :type raise_error: bool
        :rtype: bool
        :return: If the database is connected.
        :raises: DatabaseNotConnected: The database is not connected.
        """

        if not self.database:
            if raise_error:
                raise DatabaseNotConnected(
                    f"Database not connected."
                    f" Connect this manager to a database using 'connect_to_database'"
                )

            return False

        return True

    async def connect_to_database(
        self, database: Database, tables: List[str] = None
    ) -> None:
        """
        Connects to the database.
        Calls on_database_connect when connected.

        :param database: The database to connect to.
        :type database: Database
        :param tables: The tables to create (incase they do not exist).
        :type tables: List[str]
        :rtype: None
        :return: None
        """

        if not tables or len(tables) != len(self.table_identifiers):
            tables = self.table_identifiers

        for table, table_data, identifier in zip(
            tables, self.tables_column_data, self.table_identifiers
        ):
            types = generate_column_types(table_data.values(), type(database.database))

            await database.create_table(
                table, dict(zip(list(table_data), types)) if types else None, True
            )

            self.database = database
            self.tables[identifier] = table

        await self.call_event("on_database_connect")
