from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Union
)

import discord.utils
from datetime import datetime
import asyncio
from .Base import DatabaseChecker
from .Punishments import Punisher

if TYPE_CHECKING:
    import discord
    from discord.ext import commands
    from .Punishments import Punishment


class RoleError(Exception):
    """Raises error when roles are not correct"""

class Mute:
    def __init__(self, ctx: commands.Context, member: discord.Member, reason: str):
        self.muter = ctx.author
        self.member = member
        self.reason = reason
        self.guild = ctx.guild
        self.time = ctx.message.created_at  # returns datetime object


class UnMute:
    def __init__(self, ctx: commands.Context, member: discord.Member):
        self.muter = ctx.author
        self.member = member
        self.guild = ctx.guild
        self.time = ctx.message.created_at  # returns datetime object


class MuteManager(DatabaseChecker, Punisher):
    def __init__(self, bot: commands.Bot):
        super().__init__(['guild', 'member', 'timestamp_of_mute', 'timestamp_of_unmute', 'reason'],
                         ['snowflake', 'snowflake', 'snowflake', 'snowflake', 'string'])
        self.bot = bot

    async def punish(self, ctx: commands.Context, member: discord.Member, punishment: Punishment) -> None:
        await self.mute(ctx, member)

    async def mute(self, ctx: commands.Context, member: discord.Member, reason: str = "No reason provided.") -> Union[Mute, None]:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted", permissions=discord.Permissions(send_messages=False))
        if muted_role in member.roles:
            await self.call_event('on_mute_error', RoleError("User is already Muted"))
        await member.add_roles(muted_role, reason=f"Mute | {reason}")
        await self.call_event('on_mute', Mute(ctx, member, reason))
        return Mute(ctx, member, reason)

    async def unmute(self, ctx: commands.Context, member: discord.Member) -> Union[UnMute, None]:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            return
        if muted_role not in member.roles:
            await self.call_event('on_mute_error', RoleError("User is not Muted"))
        await member.remove_roles(muted_role, reason="UnMute")
        await self.call_event('on_unmute', UnMute(ctx, member))
        return UnMute(ctx, member)

    async def tempmute(self, ctx: commands.Context,
                       member: discord.Member,
                       time_of_mute: Union[int, float] = 0,
                       reason: str = "No reason provided.",
                       ):
        self._check_database()
        await self.mute(ctx, member, reason)

        await self.database.insert(self.table, {'guild': member.guild.id,
                                                'member': member.id,
                                                'timestamp_of_mute': datetime.utcnow().timestamp(),
                                                'timestamp_of_unmute': datetime.utcnow().timestamp() + time_of_mute,
                                                'reason': reason,
                                                })
        await asyncio.sleep(time_of_mute)
        await self.unmute(ctx, member)