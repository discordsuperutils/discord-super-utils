from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Iterable, TYPE_CHECKING, List

from .base import DatabaseChecker

if TYPE_CHECKING:
    import discord


@dataclass
class LevelingAccount:
    """
    Represents a LevelingAccount.
    """

    leveling_manager: LevelingManager
    member: discord.Member

    def __post_init__(self):
        self.table = self.leveling_manager.tables["xp"]

    @property
    def __checks(self):
        return LevelingManager.generate_checks(self.member)

    async def xp(self):
        xp_data = await self.leveling_manager.database.select(
            self.table, ["xp"], self.__checks
        )
        return xp_data["xp"]

    async def level(self):
        rank_data = await self.leveling_manager.database.select(
            self.table, ["rank"], self.__checks
        )
        return rank_data["rank"]

    async def next_level(self):
        level_up_data = await self.leveling_manager.database.select(
            self.table, ["level_up"], self.__checks
        )
        return level_up_data["level_up"]

    async def percentage_next_level(self):
        level_up = await self.next_level()
        xp = await self.xp()
        initial_xp = await self.initial_rank_xp()

        return min(
            abs(math.floor(abs(xp - initial_xp) / (level_up - initial_xp) * 100)), 100
        )

    async def initial_rank_xp(self):
        next_level = await self.next_level()
        return (
            0
            if next_level == 50
            else next_level / self.leveling_manager.rank_multiplier
        )

    async def set_xp(self, value):
        await self.leveling_manager.database.update(
            self.table, {"xp": value}, self.__checks
        )

    async def set_level(self, value):
        await self.leveling_manager.database.update(
            self.table, {"rank": value}, self.__checks
        )

    async def set_next_level(self, value):
        await self.leveling_manager.database.update(
            self.table, {"level_up": value}, self.__checks
        )


class LevelingManager(DatabaseChecker):
    def __init__(
        self,
        bot,
        award_role: bool = False,
        default_role_interval: int = 5,
        xp_on_message=5,
        rank_multiplier=1.5,
        xp_cooldown=60,
    ):
        super().__init__(
            [
                {
                    "guild": "snowflake",
                    "member": "snowflake",
                    "rank": "number",
                    "xp": "number",
                    "level_up": "number",
                },
                {"guild": "snowflake", "interval": "smallnumber"},
                {"guild": "snowflake", "role": "snowflake"},
            ],
            ["xp", "roles", "role_list"],
        )

        self.bot = bot
        self.award_role = award_role
        self.default_role_interval = default_role_interval
        self.xp_on_message = xp_on_message
        self.rank_multiplier = rank_multiplier
        self.xp_cooldown = xp_cooldown

        self.cooldown_members = {}
        self.add_event(self.on_database_connect)

    @DatabaseChecker.uses_database
    async def set_interval(self, guild: discord.Guild, interval: int = None) -> None:
        """
        Set the role interval of a guild.

        :param interval: The interval to set.
        :type interval: int
        :param guild: The guild to set the role interval in.
        :type guild: discord.Guild
        :return:
        :rtype: None
        """

        interval = interval if interval is not None else self.default_role_interval

        if 0 >= interval:
            raise ValueError("The interval must be greater than 0.")

        sql_insert_data = {"guild": guild.id, "interval": interval}

        await self.database.updateorinsert(
            self.tables["roles"], sql_insert_data, {"guild": guild.id}, sql_insert_data
        )

    @DatabaseChecker.uses_database
    async def get_roles(self, guild: discord.Guild) -> List[int]:
        """
        Returns the role IDs of the guild.

        :param guild: The guild to get the roles from.
        :type guild: discord.Guild
        :return:
        :rtype: List[int]
        """

        return [
            role["role"]
            for role in await self.database.select(
                self.tables["role_list"], ["role"], {"guild": guild.id}, fetchall=True
            )
        ]

    @DatabaseChecker.uses_database
    async def set_roles(
        self, guild: discord.Guild, roles: Iterable[discord.Role]
    ) -> None:
        """
        Sets the roles of the guild.

        :param guild: The guild to set the roles in.
        :type guild: discord.Guild
        :param roles: The roles to set.
        :type roles: Iterable[discord.Role]
        :return:
        :rtype: None
        """

        await self.database.delete(self.tables["role_list"], {"guild": guild.id})

        for role in roles:
            await self.database.insert(
                self.tables["role_list"], {"guild": guild.id, "role": role.id}
            )

    async def on_database_connect(self):
        self.bot.add_listener(self.__handle_experience, "on_message")

    @staticmethod
    def generate_checks(member: discord.Member):
        return {"guild": member.guild.id, "member": member.id}

    async def __handle_experience(self, message):
        self._check_database()

        if not message.guild or message.author.bot:
            return

        member_cooldown = self.cooldown_members.setdefault(message.guild.id, {}).get(
            message.author.id, 0
        )

        if (time.time() - member_cooldown) >= self.xp_cooldown:
            await self.create_account(message.author)
            member_account = await self.get_account(message.author)

            await member_account.set_xp(await member_account.xp() + self.xp_on_message)
            self.cooldown_members[message.guild.id][message.author.id] = time.time()

            leveled_up = False
            while await member_account.xp() >= await member_account.next_level():
                await member_account.set_next_level(
                    await member_account.next_level() * self.rank_multiplier
                )
                await member_account.set_level(await member_account.level() + 1)
                leveled_up = True

            if leveled_up:
                roles = []
                if self.award_role:
                    role_ids = await self.get_roles(message.guild)
                    interval = await self.database.select(
                        self.tables["roles"], ["interval"], {"guild": message.guild.id}
                    )
                    interval = (
                        interval["interval"] if interval else self.default_role_interval
                    )

                    if role_ids:
                        member_level = await member_account.level()

                        if (
                            member_level % interval == 0
                            and member_level // interval <= len(role_ids)
                        ):
                            roles = [
                                message.guild.get_role(role_id) for role_id in role_ids
                            ][: await member_account.level() // interval]
                            roles.reverse()
                            roles = [role for role in roles if role]

                await self.call_event("on_level_up", message, member_account, roles)

                if roles:
                    await message.author.add_roles(*roles)

    @DatabaseChecker.uses_database
    async def create_account(self, member):
        await self.database.insertifnotexists(
            self.tables["xp"],
            dict(
                zip(self.tables_column_data[0], [member.guild.id, member.id, 1, 0, 50])
            ),
            self.generate_checks(member),
        )

    @DatabaseChecker.uses_database
    async def get_account(self, member):
        member_data = await self.database.select(
            self.tables["xp"], [], self.generate_checks(member), True
        )

        if member_data:
            return LevelingAccount(self, member)

        return None

    @DatabaseChecker.uses_database
    async def get_leaderboard(self, guild: discord.Guild):
        guild_info = sorted(
            await self.database.select(
                self.tables["xp"], [], {"guild": guild.id}, True
            ),
            key=lambda x: x["xp"],
            reverse=True,
        )

        members = []
        for member_info in guild_info:
            member = guild.get_member(member_info["member"])
            if member:
                members.append(LevelingAccount(self, member))

        return members
