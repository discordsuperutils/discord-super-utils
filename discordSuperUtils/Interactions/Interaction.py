from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Union, Any

import discord
from discord.ext import commands
from .http import http
import aiohttp
import asyncio


class Interaction:
    def __init__(self, interaction, bot):
        self.__bot: Union[commands.Bot, discord.Client] = bot
        self.httpsession = http()
        self.event = interaction
        self.data = interaction['d']
        self.args = self.data['data']
        self.id = self.data['id']
        self.token = self.data['token']

    @property
    def guild(self) -> Optional[discord.Guild]:
        return self.__bot.get_guild(self.data['guild_id'])

    @property
    def author(self) -> Optional[discord.Member]:
        return self.guild.get_member(self.data['member']['user']['id'])

    @property
    def channel(self) -> Optional[discord.TextChannel]:
        return self.guild.get_channel(self.data['channel_id'])

    async def reply(self, text: str) -> Any:
        url = f"https://discord.com/api/v8/interactions/{self.id}/{self.token}/callback"
        data = {
            "type": 4,
            "data": {
                "content": text
            }
        }
        await self.httpsession.send(url, data=data)
