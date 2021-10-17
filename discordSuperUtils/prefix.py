from typing import Union, Any, Tuple, Iterable

import discord
from discord.ext import commands

from .base import DatabaseChecker


class PrefixManager(DatabaseChecker):
    """
    A prefix manager that manages prefixes.

    :ivar commands.Bot bot: The bot.
    :ivar Iterable[str] default_prefixes: The default prefixes.
    :ivar bool mentioned: A bool indicating if the manager should support commands.when_mentioned_or.
    :ivar dict prefix_cache: The prefix cache.
    """

    def __init__(
        self,
        bot: commands.Bot,
        default_prefixes: Iterable[str],
        mentioned: bool = False,
    ):
        super().__init__([{"guild": "snowflake", "prefix": "string"}], ["prefixes"])
        self.default_prefixes = default_prefixes
        self.bot = bot
        self.mentioned = mentioned

        self.prefix_cache = {}
        bot.command_prefix = self.__get_prefix

    @DatabaseChecker.uses_database
    async def get_prefix(self, guild: Union[discord.Guild, Any]) -> Iterable[str]:
        """
        |coro|

        Returns the prefix or the guild or the default prefixes.

        :param discord.Guild guild: The guild.
        :return: The prefixes.
        :rtype: Iterable[str]
        """

        if guild.id in self.prefix_cache:
            return self.prefix_cache[guild.id]

        prefix = await self.database.select(
            self.tables["prefixes"], ["prefix"], {"guild": guild.id}
        )
        prefix = (prefix["prefix"],) if prefix else self.default_prefixes

        self.prefix_cache[guild.id] = prefix

        return prefix

    @DatabaseChecker.uses_database
    async def delete_prefix(self, guild: discord.Guild) -> None:
        """
        |coro|

        Deletes the prefix record of the guild.

        :param discord.Guild guild: The guild.
        :return: None
        :rtype: None
        """

        self.prefix_cache.pop(guild.id)
        await self.database.delete(self.tables["prefixes"], {"guild": guild.id})

    @DatabaseChecker.uses_database
    async def set_prefix(self, guild: discord.Guild, prefix: str) -> None:
        """
        |coro|

        Sets the prefix of the guild.

        :param discord.Guild guild: The guild.
        :param str prefix: The prefix that should be set.
        :return: None
        :rtype: None
        """

        if prefix in self.default_prefixes:
            await self.delete_prefix(guild)
            return

        self.prefix_cache[guild.id] = (prefix,)
        await self.database.updateorinsert(
            self.tables["prefixes"],
            {"prefix": prefix},
            {"guild": guild.id},
            {"guild": guild.id, "prefix": prefix},
        )

    async def __get_prefix(self, bot, message: discord.Message) -> Tuple[str]:
        if not message.guild:
            return (
                commands.when_mentioned_or(*self.default_prefixes)(bot, message)
                if self.mentioned
                else self.default_prefixes
            )

        prefix = await self.get_prefix(message.guild)

        return (
            commands.when_mentioned_or(*prefix)(bot, message)
            if self.mentioned
            else prefix
        )
