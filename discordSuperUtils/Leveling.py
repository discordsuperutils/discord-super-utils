import time
import math
from .Base import EventManager, generate_column_types, DatabaseNotConnected
import asyncio


class LevelingAccount:
    def __init__(self, database, table, guild: int, member: int, rank_multiplier=1.5):
        self.database = database
        self.table = table
        self.guild = guild
        self.member = member
        self.rank_multiplier = rank_multiplier

    def __str__(self):
        return f"<Account MEMBER={self.member}, GUILD={self.guild}>"

    def __lt__(self, other):
        loop = asyncio.get_event_loop()

        current_xp = loop.run_until_complete(self.xp())  # make another way
        other_xp = loop.run_until_complete(other.xp())

        return current_xp < other_xp

    @property
    def __checks(self):
        return LevelingManager.generate_checks(self.guild, self.member)

    async def xp(self):
        xp_data = await self.database.select(self.table, ['xp'], self.__checks)
        return xp_data["xp"]

    async def level(self):
        rank_data = await self.database.select(self.table, ['rank'], self.__checks)
        return rank_data["rank"]

    async def next_level(self):
        level_up_data = await self.database.select(self.table, ['level_up'], self.__checks)
        return level_up_data["level_up"]

    async def percentage_next_level(self):
        level_up = await self.next_level()
        xp = await self.xp()
        initial_xp = await self.initial_rank_xp()

        return math.floor(abs(xp - initial_xp) / (await level_up - initial_xp) * 100)

    async def initial_rank_xp(self):
        next_level = await self.next_level()
        return 0 if next_level == 50 else await next_level / self.rank_multiplier

    async def set_xp(self, value):
        await self.database.update(self.table, {"xp": value}, self.__checks)

    async def set_level(self, value):
        await self.database.update(self.table, {"rank": value}, self.__checks)

    async def set_next_level(self, value):
        await self.database.update(self.table, {"level_up": value}, self.__checks)


class LevelingManager(EventManager):
    def __init__(self, bot, xp_on_message=5, rank_multiplier=1.5, xp_cooldown=60):
        super().__init__()
        self.database = None
        self.table = None
        self.bot = bot
        self.xp_on_message = xp_on_message
        self.rank_multiplier = rank_multiplier
        self.xp_cooldown = xp_cooldown
        self.keys = ['guild', 'member', 'rank', 'xp', 'level_up']

        self.cooldown_members = {}

    def __check_database(self):
        if not self.database:
            raise DatabaseNotConnected(f"Database not connected."
                                       f" Connect this manager to a database using {self.__class__.__name__}")

    async def connect_to_database(self, database, table):
        types = generate_column_types(['snowflake', 'snowflake', 'number', 'number', 'number'],
                                      type(database.database))

        await database.create_table(table, dict(zip(self.keys, types)) if types else None, True)

        self.database = database
        self.table = table
        self.bot.add_listener(self.__handle_experience, "on_message")

    @staticmethod
    def generate_checks(guild: int, member: int):
        return {'guild': guild, 'member': member}

    async def __handle_experience(self, message):
        self.__check_database()

        if not message.guild or message.author.bot:
            return

        if message.guild.id not in self.cooldown_members:
            self.cooldown_members[message.guild.id] = {}

        if (time.time() - self.cooldown_members[message.guild.id].get(message.author.id, 0)) >= self.xp_cooldown:
            await self.create_account(message.author)
            member_account = await self.get_account(message.author)

            await member_account.set_xp(await member_account.xp() + self.xp_on_message)
            self.cooldown_members[message.guild.id][message.author.id] = time.time()

            leveled_up = False
            while await member_account.xp() >= await member_account.next_level():
                await member_account.set_xp(await member_account.next_level() * member_account.rank_multiplier)
                await member_account.set_level(await member_account.level() + 1)
                leveled_up = True

            if leveled_up:
                await self.call_event('on_level_up', message, member_account)

    async def create_account(self, member):
        self.__check_database()

        await self.database.insertifnotexists(self.table,
                                              dict(zip(self.keys, [member.guild.id, member.id, 1, 0, 50])),
                                              self.generate_checks(member.guild.id, member.id))

    async def get_account(self, member):
        self.__check_database()

        member_data = await self.database.select(self.table, [], self.generate_checks(member.guild.id, member.id), True)

        if member_data:
            return LevelingAccount(self.database, self.table, member.guild.id, member.id, self.rank_multiplier)

        return None

    async def get_leaderboard(self, guild):
        self.__check_database()

        guild_info = await self.database.select(self.table, [], {'guild': guild.id}, True)
        members = [LevelingAccount(self.database,
                                   self.table,
                                   member_info['guild'],
                                   member_info['member'],
                                   rank_multiplier=self.rank_multiplier)
                   for member_info in guild_info]

        members.sort()
        return members
