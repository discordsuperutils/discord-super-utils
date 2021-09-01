from typing import (
    Union,
    Any
)

import discord
from discord.ext import commands

from .Base import DatabaseChecker


class PrefixManager(DatabaseChecker):
    def __init__(self, bot: commands.Bot, default_prefix: str, mentioned: bool = False):
        super().__init__([{'guild': 'snowflake', 'prefix': 'string'}], ['prefixes'])
        self.default_prefix = default_prefix
        self.bot = bot
        self.mentioned = mentioned

        self.prefix_cache = {}
        bot.command_prefix = self.__get_prefix

    async def get_prefix(self, guild: Union[discord.Guild, Any]) -> str:
        if guild.id in self.prefix_cache:
            return self.prefix_cache[guild.id]

        prefix = await self.database.select(self.tables['prefixes'], ['prefix'], {'guild': guild.id})
        prefix = prefix["prefix"] if prefix else self.default_prefix

        self.prefix_cache[guild.id] = prefix

        return prefix

    async def set_prefix(self, guild: discord.Guild, prefix: str) -> None:
        self.prefix_cache[guild.id] = prefix
        await self.database.updateorinsert(self.tables['prefixes'],
                                           {'prefix': prefix},
                                           {'guild': guild.id},
                                           {'guild': guild.id, 'prefix': prefix})

    async def __get_prefix(self, bot, message: discord.Message) -> str:
        self._check_database()

        if not message.guild:
            return commands.when_mentioned_or(self.default_prefix)(bot,
                                                                   message) if self.mentioned else self.default_prefix

        prefix = await self.get_prefix(message.guild)

        return commands.when_mentioned_or(prefix)(bot, message) if self.mentioned else prefix
