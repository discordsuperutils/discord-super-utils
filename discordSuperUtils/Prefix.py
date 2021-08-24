from typing import (
    Union,
    Any
)

import discord
from discord.ext import commands

from .Base import DatabaseChecker


class PrefixManager(DatabaseChecker):
    def __init__(self, bot: commands.Bot, default_prefix: str, mentioned: bool = False):
        super().__init__(['guild', 'prefix'], ['snowflake', 'string'])
        self.default_prefix = default_prefix
        self.bot = bot
        self.mentioned = mentioned

        bot.command_prefix = self.__get_prefix

    async def get_prefix(self, guild: Union[discord.Guild, Any]) -> str:
        prefix = await self.database.select(self.table, ['prefix'], {'guild': guild.id})

        return prefix["prefix"] if prefix else self.default_prefix

    async def set_prefix(self, guild: discord.Guild, prefix: str) -> None:
        await self.database.updateorinsert(self.table,
                                           {'prefix': prefix},
                                           {'guild': guild.id},
                                           {'guild': guild.id, 'prefix': prefix})

    async def __get_prefix(self, bot, message: discord.Message) -> str:
        self._check_database()

        if not message.guild:
            return commands.when_mentioned_or(self.default_prefix)(bot, message) if self.mentioned else self.default_prefix

        prefix = await self.get_prefix(message.guild)

        return commands.when_mentioned_or(prefix)(bot, message) if self.mentioned else prefix