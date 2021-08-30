from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Union,
    Optional
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


class AlreadyMuted(Exception):
    """Raises an error when a user is already muted."""


class MuteManager(DatabaseChecker, Punisher):
    def __init__(self, bot: commands.Bot):
        super().__init__(['guild', 'member', 'timestamp_of_mute', 'timestamp_of_unmute', 'reason'],
                         ['snowflake', 'snowflake', 'snowflake', 'snowflake', 'string'])
        self.bot = bot

        self.bot.loop.create_task(self.__check_mutes())
        self.bot.add_listener(self.on_member_join)

    async def get_muted_members(self):
        """
        This function returns all the members that are supposed to be unmuted but are muted.

        :return:
        """
        return [x for x in await self.database.select(self.table, [], fetchall=True)
                if x["timestamp_of_unmute"] <= datetime.utcnow().timestamp()]

    async def on_member_join(self, member):
        self._check_database()

        muted_members = [x for x in await self.database.select(self.table, ["timestamp_of_unmute", "member"], {
            'guild': member.guild.id,
            'member': member.id
        }, fetchall=True) if x["timestamp_of_unmute"] > datetime.utcnow().timestamp()]

        if any([muted_member["member"] == member.id for muted_member in muted_members]):
            muted_role = discord.utils.get(member.guild.roles, name="Muted")

            if muted_role:
                await member.add_roles(muted_role)

    async def __check_mutes(self) -> None:
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            if not self._check_database(False):
                await asyncio.sleep(0.01)  # Not sleeping here will break the loop resulting in discord.py not calling
                # the on ready event.
                continue

            for muted_member in await self.get_muted_members():
                guild = self.bot.get_guild(muted_member['guild'])

                if guild is None:
                    continue

                member = guild.get_member(muted_member['member'])

                if await self.unmute(member):
                    await self.call_event('on_unmute', member, muted_member["reason"])

            await asyncio.sleep(300)

    async def punish(self, ctx: commands.Context, member: discord.Member, punishment: Punishment) -> None:
        try:
            await self.mute(member)
        except discord.errors.Forbidden as e:
            raise e
        else:
            await self.call_event("on_punishment", ctx, member, punishment)

    async def mute(self,
                   member: discord.Member,
                   reason: str = "No reason provided.",
                   time_of_mute: Union[int, float] = 0) -> None:
        self._check_database()

        muted_role = discord.utils.get(member.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await member.guild.create_role(name="Muted",
                                                        permissions=discord.Permissions(send_messages=False))

        if muted_role in member.roles:
            raise AlreadyMuted(f"{member} is already muted.")

        await member.add_roles(muted_role, reason=reason)

        for channel in member.guild.channels:
            await channel.set_permissions(muted_role, send_messages=False)

        if time_of_mute <= 0:
            return

        await self.database.insert(self.table, {'guild': member.guild.id,
                                                'member': member.id,
                                                'timestamp_of_mute': datetime.utcnow().timestamp(),
                                                'timestamp_of_unmute': datetime.utcnow().timestamp() + time_of_mute,
                                                'reason': reason
                                                })

        await asyncio.sleep(time_of_mute)

        if await self.unmute(member):
            await self.call_event('on_unmute', member, reason)

    async def unmute(self, member: discord.Member) -> Optional[bool]:
        await self.database.delete(self.table, {'guild': member.guild.id, 'member': member.id})
        muted_role = discord.utils.get(member.guild.roles, name="Muted")
        if not muted_role:
            return

        if muted_role not in member.roles:
            return

        await member.remove_roles(muted_role)
        return True