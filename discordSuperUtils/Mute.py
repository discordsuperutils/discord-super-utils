from __future__ import annotations

from typing import (
    TYPE_CHECKING
)

import discord.utils

from .Base import DatabaseChecker
from .Punishments import Punisher

if TYPE_CHECKING:
    import discord
    from discord.ext import commands
    from .Punishments import Punishment


class MuteManager(DatabaseChecker, Punisher):
    def __init__(self, bot: commands.Bot):
        super().__init__(['guild', 'member', 'timestamp_of_mute', 'timestamp_of_unmute', 'reason'],
                         ['snowflake', 'snowflake', 'snowflake', 'snowflake', 'string'])
        self.bot = bot

    async def punish(self, ctx: commands.Context, member: discord.Member, punishment: Punishment) -> None:
        await self.mute(ctx, member)

    async def mute(self, ctx: commands.Context, member: discord.Member, reason: str = "No reason provided.") -> None:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            pass  # undone, don't use