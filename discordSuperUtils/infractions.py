from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING, Optional, Dict, Union

from .base import DatabaseChecker
from .punishments import Punisher, get_relevant_punishment

if TYPE_CHECKING:
    from .punishments import Punishment
    import discord
    from discord.ext import commands


__all__ = ("PartialInfraction", "Infraction", "InfractionManager")


class PartialInfraction:
    """
    A partial infraction.
    """

    def __init__(
        self,
        member: discord.Member,
        infraction_id: str,
        reason: str,
        date_of_infraction: datetime,
    ):
        self.member = member
        self.infraction_id = infraction_id
        self.reason = reason
        self.date_of_infraction = date_of_infraction


class Infraction:
    """
    An infraction object.
    """

    def __init__(
        self, database, table: str, member: discord.Member, infraction_id: str
    ):
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
        return {
            "guild": self.member.guild.id,
            "member": self.member.id,
            "id": self.infraction_id,
        }

    async def datetime(self) -> Optional[datetime]:
        timestamp_data = await self.database.select(
            self.table, ["timestamp"], self.__checks
        )
        if timestamp_data:
            return datetime.utcfromtimestamp(timestamp_data["timestamp"])

    async def reason(self) -> Optional[str]:
        reason_data = await self.database.select(self.table, ["reason"], self.__checks)
        if reason_data:
            return reason_data["reason"]

    async def set_reason(self, new_reason: str) -> None:
        await self.database.update(self.table, {"reason": new_reason}, self.__checks)

    async def delete(self) -> PartialInfraction:
        partial = PartialInfraction(
            self.member, self.infraction_id, await self.reason(), await self.datetime()
        )
        await self.database.delete(self.table, self.__checks)
        return partial


class InfractionManager(DatabaseChecker, Punisher):
    def __init__(self, bot: commands.Bot):
        super().__init__(
            [
                {
                    "guild": "snowflake",
                    "member": "snowflake",
                    "timestamp": "snowflake",
                    "id": "string",
                    "reason": "string",
                }
            ],
            ["infractions"],
        )
        self.punishments = []
        self.bot = bot

    def add_punishments(self, punishments: List[Punishment]) -> None:
        self.punishments = punishments

    async def warn(
        self, ctx: commands.Context, member: discord.Member, reason: str
    ) -> Infraction:
        self._check_database()

        generated_id = str(uuid.uuid4())
        await self.database.insert(
            self.tables["infractions"],
            {
                "guild": member.guild.id,
                "member": member.id,
                "timestamp": datetime.utcnow().timestamp(),
                "id": generated_id,
                "reason": reason,
            },
        )

        if punishment := get_relevant_punishment(
            self.punishments, len(await self.get_infractions(member))
        ):
            await punishment.punishment_manager.punish(ctx, member, punishment)

        return Infraction(
            self.database, self.tables["infractions"], member, generated_id
        )

    async def punish(
        self, ctx: commands.Context, member: discord.Member, punishment: Punishment
    ) -> None:
        await self.warn(ctx, member, punishment.punishment_reason)
        await self.call_event("on_punishment", ctx, member, punishment)

    async def get_infractions(
        self,
        member: discord.Member,
        infraction_id: str = None,
        from_timestamp: Union[int, float] = 0,
    ) -> List[Infraction]:
        self._check_database()

        checks = {"guild": member.guild.id, "member": member.id}
        if infraction_id:
            checks["id"] = infraction_id

        warnings = await self.database.select(
            self.tables["infractions"], [], checks, fetchall=True
        )

        return [
            Infraction(
                self.database, self.tables["infractions"], member, infraction["id"]
            )
            for infraction in warnings
            if infraction["timestamp"] > from_timestamp
        ]
