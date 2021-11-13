from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo
from typing import Dict, List, Optional, Any

import discord
import pytz
from discord.ext import commands

from .base import DatabaseChecker


__all__ = ("PartialBirthdayMember", "BirthdayManager", "BirthdayMember")


@dataclass
class PartialBirthdayMember:
    """
    Represents a partial birthday member.
    """

    member: discord.Member
    birthday_date: datetime
    timezone: tzinfo


@dataclass
class BirthdayMember:
    """
    Represents a birthday member.
    """

    birthday_manager: BirthdayManager
    member: discord.Member

    def __post_init__(self):
        self.table = self.birthday_manager.tables["birthdays"]

    def __hash__(self):
        return id(self)

    @property
    def __checks(self) -> Dict[str, int]:
        return {"guild": self.member.guild.id, "member": self.member.id}

    async def birthday_date(self) -> datetime:
        """
        |coro|

        Returns the birthday date in UTC of the member.

        :return: The birthday.
        :rtype: datetime
        """

        birthday_data = await self.birthday_manager.database.select(
            self.table, ["utc_birthday"], self.__checks
        )
        return datetime.fromtimestamp(
            birthday_data["utc_birthday"], await self.timezone()
        )

    async def next_birthday(self) -> datetime:
        """
        |coro|

        Returns the next birthday of the member.

        :return: The next birthday of the member.
        :rtype: datetime
        """

        current_datetime = datetime.now(await self.timezone())

        new_date = (await self.birthday_date()).replace(year=current_datetime.year)
        if new_date.timestamp() - current_datetime.timestamp() < 0:
            new_date = new_date.replace(year=current_datetime.year + 1)

        return new_date

    async def timezone(self) -> tzinfo:
        """
        |coro|

        Returns the timezone.

        :return: The timezone.
        :rtype: str
        """

        timezone_data = await self.birthday_manager.database.select(
            self.table, ["timezone"], self.__checks
        )
        return pytz.timezone(timezone_data["timezone"])

    async def delete(self) -> PartialBirthdayMember:
        """
        |coro|

        Deletes the birthday and returns a PartialBirthdayMember.

        :return: The partial birthday.
        :rtype: PartialBirthdayMember
        """

        partial = PartialBirthdayMember(
            self.member, await self.birthday_date(), await self.timezone()
        )
        await self.birthday_manager.database.delete(self.table, self.__checks)
        return partial

    async def set_birthday_date(self, timestamp: float) -> None:
        """
        |coro|

        Sets the birthday date.

        :param float timestamp: The timestamp.
        :return: None
        :rtype: None
        """

        await self.birthday_manager.database.update(
            self.table, {"utc_birthday": timestamp}, self.__checks
        )

    async def set_timezone(self, timezone: str) -> None:
        """
        |coro|

        Sets the member's timezone.

        :param str timezone: The timezone.
        :return: None
        :rtype: None
        """

        await self.birthday_manager.database.update(
            self.table, {"timezone": timezone}, self.__checks
        )

    async def age(self) -> int:
        """
        |coro|

        Returns the current age of the member.

        :return: The member age.
        :rtype: int
        """

        born = await self.birthday_date()
        today = datetime.now(await self.timezone())

        return (
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )


class BirthdayManager(DatabaseChecker):
    """
    Represents a birthday manager.
    """

    def __init__(self, bot: commands.Bot):
        """
        :param commands.Bot bot: The bot.
        """

        super().__init__(
            [
                {
                    "guild": "snowflake",
                    "member": "snowflake",
                    "utc_birthday": "snowflake",
                    "timezone": "string",
                }
            ],
            ["birthdays"],
        )
        self.bot = bot
        self.add_event(self._on_database_connect, "on_database_connect")

    async def _on_database_connect(self):
        self.bot.loop.create_task(self.__detect_birthdays())

    @DatabaseChecker.uses_database
    async def create_birthday(
        self, member: discord.Member, member_birthday: float, timezone: str = "UTC"
    ) -> None:
        """
        |coro|

        Makes a birthday for the member.

        :param discord.Member member: The member.
        :param float member_birthday: The member birthday timestamp in UTC.
        :param str timezone: The timezone.
        :return: None
        :rtype: None
        """

        await self.database.insertifnotexists(
            self.tables["birthdays"],
            dict(
                zip(
                    self.tables_column_data[0],
                    [member.guild.id, member.id, member_birthday, timezone],
                )
            ),
            {"guild": member.guild.id, "member": member.id},
        )

    @DatabaseChecker.uses_database
    async def get_birthday(self, member: discord.Member) -> Optional[BirthdayMember]:
        """
        |coro|

        Returns the BirthdayMember object of the member.

        :param discord.Member member: The member.
        :return: The BirthdayMember object if applicable.
        :rtype: Optional[BirthdayMember]
        """

        member_data = await self.database.select(
            self.tables["birthdays"],
            [],
            {"guild": member.guild.id, "member": member.id},
            True,
        )

        if member_data:
            return BirthdayMember(self, member)

        return None

    @DatabaseChecker.uses_database
    async def get_upcoming(self, guild: discord.Guild) -> List[BirthdayMember]:
        """
        |coro|

        Returns the upcoming birthdays in the guild.

        :param discord.Guild guild: The guild.
        :return: The birthdays, sorted by their nearest birthday date.
        :rtype: List[BirthdayMember]
        """

        member_data = await self.database.select(
            self.tables["birthdays"], [], {"guild": guild.id}, fetchall=True
        )

        birthdays = {}

        for birthday_member in member_data:
            member = guild.get_member(birthday_member["member"])

            if member:
                birthday = BirthdayMember(self, member)
                birthdays[birthday] = await birthday.next_birthday()
                # Did this instead of running the method until complete in the sorted key lambda

        return sorted(birthdays, key=lambda x: birthdays[x])

    @staticmethod
    def get_midnight_timezones() -> List[str]:
        """
        This method returns a list of timezones where the current time is 12 am.

        :return: The list of timezones.
        :rtype: List[str]
        """

        current_utc_time = datetime.utcnow()
        utc_offset = -(current_utc_time.hour % 24)

        minutes = 30 if current_utc_time.minute > 5 else 0
        if minutes == 30:
            utc_offset -= 1

        checks = (
            timedelta(hours=utc_offset, minutes=minutes),
            timedelta(
                hours=24 - -utc_offset if current_utc_time.hour != 0 else 0,
                minutes=minutes,
            ),
        )

        return [
            tz.zone
            for tz in map(pytz.timezone, pytz.all_timezones_set)
            if current_utc_time.astimezone(tz).utcoffset() in checks
        ]

    @DatabaseChecker.uses_database
    async def get_members_with_birthday(
        self, timezones: List[str]
    ) -> List[Dict[str, Any]]:
        """
        |coro|

        This function receives a list of timezones and returns a list of members that have birthdays in that date
        and timezone.

        :param List[str] timezones: The timezones.
        :return: Returns the members that have a birthday.
        :rtype: List[Dict[str, Any]]
        """

        result_members = []
        registered_members = await self.database.select(
            self.tables["birthdays"], [], fetchall=True
        )

        birthday_members = [x for x in registered_members if x["timezone"] in timezones]
        for birthday_member in birthday_members:
            timezone_time = datetime.now(pytz.timezone(birthday_member["timezone"]))
            date_of_birth = datetime.fromtimestamp(birthday_member["utc_birthday"])

            if (
                date_of_birth.month == timezone_time.month
                and date_of_birth.day == timezone_time.day
            ):
                result_members.append(birthday_member)

        return result_members

    @staticmethod
    def round_to_nearest(timedelta_to_round: timedelta) -> float:
        """
        This function receives a timedelta to round to and gets the amount of seconds before that timestamp.

        :param timedelta timedelta_to_round: The timedelta to round to.
        :return: The seconds until the nearest rounded timedelta.
        :rtype: float
        """

        now = datetime.now()
        nearest = now + (datetime.min - now) % timedelta_to_round
        return nearest.timestamp() - now.timestamp()

    async def __detect_birthdays(self) -> None:
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            await asyncio.sleep(self.round_to_nearest(timedelta(minutes=30)))

            for birthday_member in await self.get_members_with_birthday(
                self.get_midnight_timezones()
            ):
                guild = self.bot.get_guild(birthday_member["guild"])

                if guild:
                    member = guild.get_member(birthday_member["member"])

                    if member:
                        await self.call_event(
                            "on_member_birthday", BirthdayMember(self, member)
                        )
