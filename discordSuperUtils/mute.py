from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Union, Optional, List, Any, Dict

import discord
import discord.utils

from .base import DatabaseChecker
from .punishments import Punisher

if TYPE_CHECKING:
    from discord.ext import commands
    from .punishments import Punishment


__all__ = ("AlreadyMuted", "MuteManager")


class AlreadyMuted(Exception):
    """Raises an error when a user is already muted."""


class MuteManager(DatabaseChecker, Punisher):
    """
    A MuteManager that handles mutes for guilds.
    """

    __slots__ = ("bot",)

    def __init__(self, bot: commands.Bot, muted_role_name: str = "Muted") -> None:
        super().__init__(
            [
                {
                    "guild": "snowflake",
                    "member": "snowflake",
                    "timestamp_of_mute": "snowflake",
                    "timestamp_of_unmute": "snowflake",
                    "reason": "string",
                }
            ],
            ["mutes"],
        )
        self.bot = bot
        self.muted_role_name = muted_role_name

        self.add_event(self.on_database_connect)

    async def on_database_connect(self):
        self.bot.loop.create_task(self.__check_mutes())
        self.bot.add_listener(self.on_member_join)

    @DatabaseChecker.uses_database
    async def get_muted_members(self) -> List[Dict[str, Any]]:
        """
        |coro|

        This function returns all the members that are supposed to be unmuted but are muted.

        :return: The unmuted members.
        :rtype: List[Dict[str, Any]]
        """

        return [
            x
            for x in await self.database.select(self.tables["mutes"], [], fetchall=True)
            if x["timestamp_of_unmute"] <= datetime.utcnow().timestamp()
        ]

    async def on_member_join(self, member: discord.Member) -> None:
        """
        |coro|

        The on_member_join event callback.
        Used so the member cant leave the guild, join back and be unmuted.

        :param member: The member that joined.
        :type member: discord.Member
        :return: None
        :rtype: None
        """

        self._check_database()  # Not using the decorator as it breaks the coroutine check

        muted_members = [
            x
            for x in await self.database.select(
                self.tables["mutes"],
                ["timestamp_of_unmute", "member"],
                {"guild": member.guild.id, "member": member.id},
                fetchall=True,
            )
            if x["timestamp_of_unmute"] > datetime.utcnow().timestamp()
        ]

        if any([muted_member["member"] == member.id for muted_member in muted_members]):
            muted_role = discord.utils.get(
                member.guild.roles, name=self.muted_role_name
            )

            if muted_role:
                await member.add_roles(muted_role)

    async def __check_mutes(self) -> None:
        """
        |coro|

        A loop that makes sure the members are unmuted when they are supposed to.

        :return: None
        :rtype: None
        """

        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            for muted_member in await self.get_muted_members():
                guild = self.bot.get_guild(muted_member["guild"])

                if guild is None:
                    continue

                member = guild.get_member(muted_member["member"])

                if await self.unmute(member):
                    await self.call_event("on_unmute", member, muted_member["reason"])

            await asyncio.sleep(300)

    async def punish(
        self, ctx: commands.Context, member: discord.Member, punishment: Punishment
    ) -> None:
        try:
            await self.mute(member)
        except discord.errors.Forbidden as e:
            raise e
        else:
            await self.call_event("on_punishment", ctx, member, punishment)

    @staticmethod
    async def ensure_permissions(
        guild: discord.Guild, muted_role: discord.Role
    ) -> None:
        """
        |coro|

        This function loops through the guild's channels and ensures the muted_role is not allowed to
        send messages or speak in that channel.

        :param guild: The guild to get the channels from.
        :type guild: discord.Guild
        :param muted_role: The muted role.
        :type muted_role: discord.Role
        :return: None
        """

        channels_to_mute = [
            channel
            for channel in guild.channels
            if channel.overwrites_for(muted_role).send_messages is not False
        ]
        # Now, you might say what the heck, why don't you test if the value is True instead of checking if it
        # is not False? I am doing it this way because permissions have 3 values,
        # None, True and False.
        # Now, lets say we have a permission that is set to None, if i test it for a False value, (if not value) it will
        # return False which is incorrect and it should return True.

        await asyncio.gather(
            *[
                channel.set_permissions(muted_role, send_messages=False, speak=False)
                for channel in channels_to_mute
            ]
        )

    async def __handle_unmute(
        self, time_of_mute: Union[int, float], member: discord.Member, reason: str
    ) -> None:
        """
        |coro|

        A function that handles the member's unmute that runs separately from mute so it wont be blocked.

        :param time_of_mute: The time until the member's unmute timestamp.
        :type time_of_mute: Union[int, float]
        :param member: The member to unmute.
        :type member: discord.Member
        :param reason: The reason of the mute.
        :type reason: str
        :return: None
        """

        await asyncio.sleep(time_of_mute)

        if await self.unmute(member):
            await self.call_event("on_unmute", member, reason)

    @DatabaseChecker.uses_database
    async def mute(
        self,
        member: discord.Member,
        reason: str = "No reason provided.",
        time_of_mute: Union[int, float] = 0,
    ) -> None:
        """
        |coro|

        Mutes a member.

        :raises: AlreadyMuted: The member is already muted.
        :param member: The member to mute.
        :type member: discord.Member
        :param reason: The reason of the mute.
        :type reason: str
        :param time_of_mute: The time of mute.
        :type time_of_mute: Union[int, float]
        :return: None,
        :rtype: None
        """

        muted_role = discord.utils.get(member.guild.roles, name=self.muted_role_name)
        if not muted_role:
            muted_role = await member.guild.create_role(
                name="Muted",
                permissions=discord.Permissions(send_messages=False, speak=False),
            )

        if muted_role in member.roles:
            raise AlreadyMuted(f"{member} is already muted.")

        await member.add_roles(muted_role, reason=reason)

        self.bot.loop.create_task(self.ensure_permissions(member.guild, muted_role))

        if time_of_mute <= 0:
            return

        await self.database.insert(
            self.tables["mutes"],
            {
                "guild": member.guild.id,
                "member": member.id,
                "timestamp_of_mute": datetime.utcnow().timestamp(),
                "timestamp_of_unmute": datetime.utcnow().timestamp() + time_of_mute,
                "reason": reason,
            },
        )

        self.bot.loop.create_task(self.__handle_unmute(time_of_mute, member, reason))

    @DatabaseChecker.uses_database
    async def unmute(self, member: discord.Member) -> Optional[bool]:
        """
        |coro|

        Unmutes a member.

        :param member: The member to unmute.
        :type member: discord.Member
        :rtype: Optional[bool]
        :return: A bool indicating if the unmute was successful
        """

        await self.database.delete(
            self.tables["mutes"], {"guild": member.guild.id, "member": member.id}
        )
        muted_role = discord.utils.get(member.guild.roles, name=self.muted_role_name)
        if not muted_role:
            return

        if muted_role not in member.roles:
            return

        await member.remove_roles(muted_role)
        return True
