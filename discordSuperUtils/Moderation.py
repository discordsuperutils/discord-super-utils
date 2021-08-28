from __future__ import annotations
from datetime import datetime, timedelta
import asyncio
import discord

from .Base import DatabaseChecker, EventManager
import uuid
from typing import (
    Dict,
    Optional,
    List,
    Union,
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from discord.ext import commands


class Punishment:
    def __init__(self,
                 punishment_manager,
                 punish_after: int = 3,
                 punishment_reason: str = "No reason specified.",
                 punishment_time: timedelta = timedelta(days=1)):
        self.punishment_manager = punishment_manager
        self.punish_after = punish_after
        self.punishment_reason = punishment_reason
        self.punishment_time = punishment_time

        if type(punishment_manager) not in MANAGERS:
            raise TypeError(f"Manager of type '{type(punishment_time)} is not supported.'")


def get_relevant_punishment(punishments: List[Punishment], punish_count: int) -> Optional[Punishment]:
    return {x.punish_after: x for x in punishments}.get(punish_count)


class KickManager(EventManager):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def punish(self, ctx: commands.Context, member: discord.Member, punishment: Punishment) -> None:
        await member.kick(reason=punishment.punishment_reason)
        await self.call_event("on_punishment", ctx, member, punishment)


class BanManager(DatabaseChecker):
    def __init__(self, bot: commands.Bot):
        super().__init__(['guild', 'member', 'reason', 'timestamp'], ['snowflake', 'snowflake', 'string', 'snowflake'])
        self.bot = bot

        self.bot.loop.create_task(self.__check_bans())

    async def get_banned_members(self):
        """
        This function returns all the members that are supposed to be unbanned but are banned.

        :return:
        """
        return [x for x in await self.database.select(self.table, [], fetchall=True)
                if x["timestamp"] < datetime.utcnow().timestamp()]

    async def __check_bans(self) -> None:
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            if not self._check_database(False):
                await asyncio.sleep(0.01)  # Not sleeping here will break the loop resulting in discord.py not calling
                # the on ready event.
                continue

            for banned_member in await self.get_banned_members():
                guild = self.bot.get_guild(banned_member['guild'])

                if guild is None:
                    continue

                user = await self.bot.fetch_user(banned_member['member'])

                if await self.unban(user, guild):
                    await self.call_event("on_unban", user, banned_member['reason'])

            await asyncio.sleep(300)

    async def punish(self, ctx: commands.Context, member: discord.Member, punishment: Punishment) -> None:
        self.bot.loop.create_task(
            self.ban(member, punishment.punishment_reason, punishment.punishment_time.total_seconds())
        )
        await self.call_event("on_punishment", ctx, member, punishment)

    @staticmethod
    async def get_ban(member: Union[discord.Member, discord.User],
                      guild: discord.Guild) -> Optional[discord.User]:
        banned = await guild.bans()
        for x in banned:
            if x.user.id == member.id:
                return x.user

    async def unban(self, member: Union[discord.Member, discord.User], guild: discord.Guild = None) -> bool:
        guild = guild if guild is not None else member.guild
        await self.database.delete(self.table, {'guild': guild.id, 'member': member.id})

        if user := await self.get_ban(member, guild):
            await guild.unban(user)
            return True

    async def ban(self,
                  member: discord.Member,
                  reason: str = "No reason provided.",
                  time_of_ban: Union[int, float] = 0) -> None:
        self._check_database()

        await member.ban(reason=reason)

        if time_of_ban <= 0:
            return

        await self.database.insert(self.table, {'guild': member.guild.id,
                                                'member': member.id,
                                                'reason': reason,
                                                'timestamp': datetime.utcnow().timestamp() + time_of_ban})

        await asyncio.sleep(time_of_ban)

        if await self.unban(member):
            await self.call_event("on_unban", member, reason)


class PartialInfraction:
    def __init__(self, member: discord.Member, infraction_id: str, reason: str, date_of_infraction: datetime):
        self.member = member
        self.infraction_id = infraction_id
        self.reason = reason
        self.date_of_infraction = date_of_infraction


class Infraction:
    def __init__(self, database, table: str, member: discord.Member, infraction_id: str):
        self.member = member
        self.database = database
        self.table = table
        self.infraction_id = infraction_id

    def __str__(self):
        return f"<Infraction {self.infraction_id=}>"

    def __repr__(self):
        return f"<Infraction {self.member=}, {self.infraction_id=}>"

    @property
    def __checks(self) -> Dict[str, int]:
        return {'guild': self.member.guild.id, 'member': self.member.id, 'id': self.infraction_id}

    async def datetime(self) -> Optional[datetime]:
        timestamp_data = await self.database.select(self.table, ['timestamp'], self.__checks)
        if timestamp_data:
            return datetime.utcfromtimestamp(timestamp_data["timestamp"])

    async def reason(self) -> Optional[str]:
        reason_data = await self.database.select(self.table, ['reason'], self.__checks)
        if reason_data:
            return reason_data["reason"]

    async def set_reason(self, new_reason: str) -> None:
        await self.database.update(self.table, {'reason': new_reason}, self.__checks)

    async def delete(self) -> PartialInfraction:
        partial = PartialInfraction(self.member, self.infraction_id, await self.reason(), await self.datetime())
        await self.database.delete(self.table, self.__checks)
        return partial


class InfractionManager(DatabaseChecker):
    def __init__(self, bot: commands.Bot):
        super().__init__(['guild', 'member', 'timestamp', 'id', 'reason'],
                         ['snowflake', 'snowflake', 'snowflake', 'string', 'string'])
        self.punishments = []
        self.bot = bot

    def add_punishments(self, punishments: List[Punishment]) -> None:
        self.punishments = punishments

    async def warn(self, ctx: commands.Context, member: discord.Member, reason: str) -> Infraction:
        self._check_database()

        generated_id = str(uuid.uuid4())
        await self.database.insert(self.table, {
            'guild': member.guild.id,
            'member': member.id,
            'timestamp': datetime.utcnow().timestamp(),
            'id': generated_id,
            'reason': reason
        })

        if punishment := get_relevant_punishment(self.punishments, len(await self.get_infractions(member))):
            await punishment.punishment_manager.punish(ctx, member, punishment)

        return Infraction(self.database, self.table, member, generated_id)

    async def punish(self, ctx: commands.Context, member: discord.Member, punishment: Punishment) -> None:
        await self.warn(ctx, member, punishment.punishment_reason)
        await self.call_event("on_punishment", ctx, member, punishment)

    async def get_infractions(self,
                              member: discord.Member,
                              infraction_id: str = None,
                              from_timestamp: Union[int, float] = 0) -> List[Infraction]:
        self._check_database()

        checks = {'guild': member.guild.id, 'member': member.id}
        if infraction_id:
            checks['id'] = infraction_id

        warnings = await self.database.select(self.table, [], checks, fetchall=True)

        return [Infraction(self.database,
                           self.table,
                           member,
                           infraction['id']) for infraction in warnings if infraction['timestamp'] > from_timestamp]


MANAGERS = [BanManager, InfractionManager, KickManager]