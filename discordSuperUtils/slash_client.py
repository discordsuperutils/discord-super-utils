from __future__ import annotations

import discord
from discord import app_commands
import typing

if typing.TYPE_CHECKING:
    from typing import List

__all__ = (
    "SlashClient",
)


class SlashClient(discord.Client):
    def __init__(self, sync_guilds: List[int], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sync_guilds = sync_guilds
        self.synced = False
        self.tree = app_commands.CommandTree(self)

    def create_guild_objects(self) -> List[discord.Object]:
        return [discord.Object(id=guild_id) for guild_id in self.sync_guilds]

    async def sync(self):
        if self.synced:
            return

        for guild in self.create_guild_objects():
            await self.tree.sync(guild=guild)
        self.synced = True
