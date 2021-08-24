from datetime import datetime, timedelta
import asyncio
import pytz
import discord
from discord.ext import commands
from typing import (
    Dict,
    List,
    Optional
)

from .Base import DatabaseChecker


class BirthdayMember:
    def __init__(self, database, table: str, member: discord.Member):
        self.database = database
        self.table = table
        self.member = member

    @property
    def __checks(self) -> Dict[str, int]:
        return {'guild': self.member.guild.id, 'member': self.member.id}

    async def birthday_date(self) -> datetime:
        birthday_data = await self.database.select(self.table, ["utc_birthday"], self.__checks)
        return datetime.utcfromtimestamp(birthday_data["utc_birthday"])

    async def timezone(self) -> str:
        timezone_data = await self.database.select(self.table, ["timezone"], self.__checks)
        return timezone_data["timezone"]

    async def set_birthday_date(self, timestamp: float) -> None:
        await self.database.update(self.table, {"utc_birthday": timestamp}, self.__checks)

    async def set_timezone(self, timezone: str) -> None:
        await self.database.update(self.table, {"timezone": timezone}, self.__checks)

    async def age(self) -> int:
        current_birthday = await self.birthday_date()
        current_datetime = datetime.now()

        return current_datetime.year - current_birthday.year - (datetime(year=current_datetime.year,
                                                                         month=current_birthday.month,
                                                                         day=current_birthday.day) >= current_datetime)


class BirthdayManager(DatabaseChecker):
    def __init__(self, bot: commands.Bot):
        super().__init__(['guild', 'member', 'utc_birthday', 'timezone'],
                         ['snowflake', 'snowflake', 'snowflake', 'smallnumber'])
        self.bot = bot
        self.bot.loop.create_task(self.__detect_birthdays())

    async def create_birthday(self,
                              member: discord.Member,
                              member_birthday: float,
                              timezone: str = "UTC") -> None:
        self._check_database()

        await self.database.insertifnotexists(self.table,
                                              dict(zip(self.column_names,
                                                       [member.guild.id, member.id, member_birthday, timezone])),
                                              {'guild': member.guild.id, 'member': member.id})

    async def get_birthday(self, member: discord.Member) -> Optional[BirthdayMember]:
        self._check_database()

        member_data = await self.database.select(self.table, [], {'guild': member.guild.id, 'member': member.id}, True)

        if member_data:
            return BirthdayMember(self.database, self.table, member)

        return None

    async def get_upcoming(self, guild: discord.Guild) -> List[BirthdayMember]:
        self._check_database()

        member_data = await self.database.select(self.table, [], fetchall=True)
        current_datetime = datetime.utcnow()

        member_data_formatted = []
        for member in member_data:
            member["utc_birthday"] = datetime.utcfromtimestamp(member["utc_birthday"])

            new_date = member["utc_birthday"].replace(year=current_datetime.year)
            if new_date.timestamp() - current_datetime.timestamp() < 0:
                new_date = new_date.replace(year=current_datetime.year + 1)

            member["utc_birthday"] = new_date

            member_data_formatted.append(member)

        birthdays = []
        for birthday_member in sorted(member_data_formatted, key=lambda x: x["utc_birthday"]):
            member = guild.get_member(birthday_member['member'])

            if member:
                birthdays.append(BirthdayMember(self.database, self.table, member))

        return birthdays

    async def __detect_birthdays(self) -> None:
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            if not self._check_database(False):
                await asyncio.sleep(0.01)  # Not sleeping here will break the loop resulting in discord.py not calling
                # the on ready event.
                continue

            now = datetime.now()
            nearest = now + (datetime.min - now) % timedelta(minutes=30)

            rounded = nearest.timestamp() - now.timestamp()

            await asyncio.sleep(rounded)

            current_utc_time = datetime.utcnow()
            utc_offset = -(current_utc_time.hour % 24)

            minutes = 30 if current_utc_time.minute > 5 else 0
            checks = (
                timedelta(hours=utc_offset, minutes=minutes),
                timedelta(hours=24 - (current_utc_time.hour % 24) if current_utc_time.hour != 0 else 0, minutes=minutes)
            )

            timezones = [tz.zone for tz in map(pytz.timezone, pytz.all_timezones_set)
                         if current_utc_time.astimezone(tz).utcoffset() in checks]

            registered_members = await self.database.select(self.table, [], fetchall=True)
            # add SQL custom to make OR statement

            birthday_members = [x for x in registered_members if x["timezone"] in timezones]
            for birthday_member in birthday_members:
                timezone_time = datetime.now(pytz.timezone(birthday_member["timezone"]))
                date_of_birth = datetime.fromtimestamp(birthday_member["utc_birthday"])

                if date_of_birth.month == timezone_time.month and date_of_birth.day == timezone_time.day:
                    guild = self.bot.get_guild(birthday_member["guild"])

                    if guild:
                        member = guild.get_member(birthday_member["member"])

                        if member:
                            await self.call_event("on_member_birthday", BirthdayMember(
                                self.database, self.table, member
                            ))
