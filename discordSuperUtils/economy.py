from __future__ import annotations

from dataclasses import dataclass

import discord
from typing import List, Optional

from .base import DatabaseChecker


@dataclass
class EconomyAccount:
    """
    Represents an EconomyAccount.
    """

    economy_manager: EconomyManager
    member: discord.Member

    def __post_init__(self):
        self.table = self.economy_manager.tables["economy"]

    @property
    def __checks(self):
        return EconomyManager.generate_checks(self.member)

    async def currency(self):
        currency_data = await self.economy_manager.database.select(
            self.table, ["currency"], self.__checks
        )
        return currency_data["currency"]

    async def bank(self):
        bank_data = await self.economy_manager.database.select(
            self.table, ["bank"], self.__checks
        )
        return bank_data["bank"]

    async def net(self):
        return await self.bank() + await self.currency()

    async def change_currency(self, amount: int):
        currency = await self.currency()
        await self.economy_manager.database.update(
            self.table, {"currency": currency + amount}, self.__checks
        )

    async def change_bank(self, amount: int):
        bank_amount = await self.bank()
        await self.economy_manager.database.update(
            self.table, {"bank": bank_amount + amount}, self.__checks
        )


class EconomyManager(DatabaseChecker):
    def __init__(self, bot):
        super().__init__(
            [
                {
                    "guild": "snowflake",
                    "member": "snowflake",
                    "currency": "snowflake",
                    "bank": "snowflake",
                }
            ],
            ["economy"],
        )
        self.bot = bot

    @staticmethod
    def generate_checks(member: discord.Member):
        return {"guild": member.guild.id, "member": member.id}

    async def create_account(self, member: discord.Member) -> None:
        self._check_database()

        await self.database.insertifnotexists(
            self.tables["economy"],
            {"guild": member.guild.id, "member": member.id, "currency": 0, "bank": 0},
            self.generate_checks(member),
        )

    async def get_account(self, member: discord.Member) -> Optional[EconomyAccount]:
        self._check_database()

        member_data = await self.database.select(
            self.tables["economy"],
            [],
            self.generate_checks(member),
            True,
        )

        if member_data:
            return EconomyAccount(self, member)

        return None

    @DatabaseChecker.uses_database
    async def get_leaderboard(self, guild: discord.Guild) -> List[EconomyAccount]:
        guild_info = sorted(
            await self.database.select(
                self.tables["economy"], [], {"guild": guild.id}, True
            ),
            key=lambda x: x["bank"] + x["currency"],
            reverse=True,
        )

        members = []
        for member_info in guild_info:
            member = guild.get_member(member_info["member"])
            if member:
                members.append(EconomyAccount(self, member))

        return members
