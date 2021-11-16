from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Optional, TYPE_CHECKING, List, Tuple

from discord.ext import commands

if TYPE_CHECKING:
    from .base import DatabaseChecker
    from .database import Database

__all__ = ("ExtendedClient", "DatabaseClient", "ManagerClient")


class ExtendedClient(commands.Bot):
    """
    Represents an extended commands,Bot client.
    Adds a token attribute, replaces methods, loads cogs, etc.
    """

    __slots__ = ("token", "start_time")

    def __init__(self, token: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = token
        self.start_time = time.time()

    def load_cogs(self, directory: str, ignore_prefix: str = "__") -> None:
        """
        Loads all the cog extensions in the directory.

        :param str ignore_prefix: The prefix to ignore, files that start with that prefix will not be loaded.
        :param str directory: The directory.
        :return: None
        :rtype: None
        """

        extension_directory = directory.replace("/", ".")
        if extension_directory:
            extension_directory += "."

        working_directory = os.getcwd()

        slash = "/" if "/" in working_directory else "\\"

        for file in os.listdir(working_directory + f"{slash}{directory}"):
            if not file.endswith(".py") or file.startswith(ignore_prefix):
                continue

            try:
                self.load_extension(f"{extension_directory}{file.replace('.py', '')}")
                logging.info(f"Loaded cog {file}")
            except Exception as e:
                logging.error(f"Failed to load cog {file}")
                raise e

    def run(self, cogs_directory: Optional[str] = "cogs") -> None:
        """
        Runs the bot and loads the cogs automatically.

        :param Optional[str] cogs_directory: The directory to load the cogs from.
        :return: None
        :rtype: None
        """

        if cogs_directory is not None:  # Might be an empty string.
            self.load_cogs(cogs_directory)

        super().run(self.token)


class DatabaseClient(ExtendedClient):
    """
    Represents an extended client that has a database.
    """

    __slots__ = ("database",)

    def __init__(self, token: str, *args, **kwargs):
        super().__init__(token, *args, **kwargs)
        self.database: Optional[Database] = None

    async def wait_until_database_connection(self) -> None:
        """
        Waits until the database is connected.

        :return: None
        :rtype: None
        """

        while not self.database:
            await asyncio.sleep(0.1)


class ManagerClient(DatabaseClient):
    """
    Represents an extended database client that has managers.
    """

    __slots__ = ("managers",)

    def __init__(self, token: str, *args, **kwargs):
        super().__init__(token, *args, **kwargs)
        self.managers: List[Tuple[DatabaseChecker, Optional[List[str]]]] = []

        self.add_listener(self.on_ready)  # Doesnt do this automatically.

    def add_manager(self, manager: DatabaseChecker, tables: List[str] = None) -> None:
        self.managers.append((manager, tables))

    async def on_ready(self):
        await self.wait_until_database_connection()

        for manager, tables in self.managers:
            await manager.connect_to_database(self.database, tables or [])
