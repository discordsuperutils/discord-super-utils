from __future__ import annotations

from typing import TYPE_CHECKING

from .Base import EventManager
from .Punishments import Punisher

if TYPE_CHECKING:
    from discord.ext import commands
    import discord
    from .Punishments import Punishment


class KickManager(EventManager, Punisher):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def punish(self, ctx: commands.Context, member: discord.Member, punishment: Punishment) -> None:
        try:
            await member.kick(reason=punishment.punishment_reason)
        except discord.errors.Forbidden as e:
            raise e
        else:
            await self.call_event("on_punishment", ctx, member, punishment)