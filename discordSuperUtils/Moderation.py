import discord
from discord.ext import commands
import time
from datetime import datetime

from .Base import DatabaseChecker
import uuid
from enum import Enum
from typing import (
    Dict,
    Optional,
    List,
    Union
)


class PunishmentTypes(Enum):
    pass


class Punishment:
    # I was not done yash
    def __init__(self):
        pass


class BanManager:
    def __init__(self, bot):
        self.bot = bot
        self.bans = []
        self._tempbans = []


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
            return datetime.fromtimestamp(timestamp_data["timestamp"])

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

        self.bot = bot

    async def warn(self, member: discord.Member, reason: str) -> Infraction:
        self._check_database()

        generated_id = str(uuid.uuid4())
        await self.database.insert(self.table, {
            'guild': member.guild.id,
            'member': member.id,
            'timestamp': time.time(),
            'id': generated_id,
            'reason': reason
        })

        return Infraction(self.database, self.table, member, generated_id)

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