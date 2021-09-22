import discord
from typing import List, Optional

from .base import DatabaseChecker


class EconomyAccount:
    def __init__(self, guild: int, member: int, database, table):
        self.guild = guild
        self.member = member
        self.database = database
        self.table = table

    def __str__(self):
        return f"<Account MEMBER={self.member}, GUILD={self.guild}>"

    @property
    def __checks(self):
        return EconomyManager.generate_checks(self.guild, self.member)

    async def currency(self):
        currency_data = await self.database.select(
            self.table, ["currency"], self.__checks
        )
        return currency_data["currency"]

    async def bank(self):
        bank_data = await self.database.select(self.table, ["bank"], self.__checks)
        return bank_data["bank"]

    async def net(self):
        return await self.bank() + await self.currency()

    async def change_currency(self, amount: int):
        currency = await self.currency()
        await self.database.update(
            self.table, {"currency": currency + amount}, self.__checks
        )

    async def change_bank(self, amount: int):
        bank_amount = await self.bank()
        await self.database.update(
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
    def generate_checks(guild: int, member: int):
        return {"guild": guild, "member": member}

    async def create_account(self, member: discord.Member) -> None:
        self._check_database()

        await self.database.insertifnotexists(
            self.tables["economy"],
            {"guild": member.guild.id, "member": member.id, "currency": 0, "bank": 0},
            self.generate_checks(member.guild.id, member.id),
        )

    async def get_account(self, member: discord.Member) -> Optional[EconomyAccount]:
        self._check_database()

        member_data = await self.database.select(
            self.tables["economy"],
            [],
            self.generate_checks(member.guild.id, member.id),
            True,
        )

        if member_data:
            return EconomyAccount(
                member.guild.id, member.id, self.database, self.tables["economy"]
            )

        return None

    async def get_leaderboard(self, guild) -> List[EconomyAccount]:
        self._check_database()

        guild_info = await self.database.select(
            self.tables["economy"], [], {"guild": guild.id}, True
        )
        members = [
            EconomyAccount(
                member_info["guild"],
                member_info["member"],
                database=self.database,
                table=self.tables["economy"],
            )
            for member_info in sorted(
                guild_info, key=lambda x: x["bank"] + x["currency"], reverse=True
            )
        ]

        return members
