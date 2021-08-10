from .Database import DatabaseManager
import time
import math
from .Base import EventManager
import asyncio


database_keys = ['guild', 'member', 'rank', 'xp', 'level_up']


class LevelingAccount:
    def __init__(self, database: DatabaseManager, table, guild: int, member: int, rank_multiplier=1.5):
        self.database = database
        self.table = table
        self.guild = guild
        self.member = member
        self.rank_multiplier = rank_multiplier

    def __str__(self):
        return f"<Account MEMBER={self.member}, GUILD={self.guild}>"

    def __repr__(self):
        return f"<Account GUILD={self.guild}, MEMBER={self.member}, XP={self.xp}, LEVEL={self.level}>"

    def __lt__(self, other):
        return self.xp < other.xp

    @property
    def __checks(self):
        return LevelingManager.generate_checks(self.guild, self.member)

    @property
    def xp(self):
        return self.database.select(['xp'], self.table, self.__checks)[0]

    @property
    def level(self):
        return self.database.select(['rank'], self.table, self.__checks)[0]

    @property
    def next_level(self):
        return self.database.select(['level_up'], self.table, self.__checks)[0]

    @property
    def percentage_next_level(self):
        return math.floor(abs(self.xp - self.initial_rank_xp) / (self.next_level - self.initial_rank_xp) * 100)

    @property
    def initial_rank_xp(self):
        return 0 if self.next_level == 50 else self.next_level / self.rank_multiplier

    @xp.setter
    def xp(self, value):
        self.database.update(['xp'], [value], self.table, self.__checks)

    @level.setter
    def level(self, value):
        self.database.update(['rank'], [value], self.table, self.__checks)

    @next_level.setter
    def next_level(self, value):
        self.database.update(['level_up'], [value], self.table, self.__checks)


class LevelingManager(EventManager):
    def __init__(self, database: DatabaseManager, table, bot, xp_on_message=5, rank_multiplier=1.5, xp_cooldown=60):
        super().__init__()
        self.database = database
        self.table = table
        self.bot = bot
        self.xp_on_message = xp_on_message
        self.rank_multiplier = rank_multiplier
        self.xp_cooldown = xp_cooldown

        self.cooldown_members = {}
        self.bot.add_listener(self.__handle_experience, "on_message")
        self.database.createtable(self.table, [{'name': key, 'type': 'INTEGER'} for key in database_keys], True)

    @staticmethod
    def generate_checks(guild: int, member: int):
        return [{'guild': guild}, {'member': member}]

    async def __handle_experience(self, message):
        if not message.guild or message.author.bot:
            return

        if message.guild.id not in self.cooldown_members:
            self.cooldown_members[message.guild.id] = {}

        self.create_account(message.author)
        member_account = self.get_account(message.author)
        member_timestamp = self.cooldown_members[message.guild.id].get(message.author.id, 0)

        if (time.time() - member_timestamp) >= self.xp_cooldown:
            member_account.xp += self.xp_on_message
            self.cooldown_members[message.guild.id][message.author.id] = time.time()

            leveled_up = False
            while member_account.xp >= member_account.next_level:
                member_account.next_level *= member_account.rank_multiplier
                member_account.level += 1
                leveled_up = True

            if leveled_up:
                loop = asyncio.get_event_loop()
                loop.create_task(self.call_event('on_level_up', message, member_account))

    def create_account(self, member):
        self.database.insertifnotexists(database_keys, [member.guild.id, member.id, 1, 0, 50],
                                        self.table, [{'guild': member.guild.id}, {'member': member.id}])

    def get_account(self, member):
        member_data = self.database.select([], self.table, self.generate_checks(member.guild.id, member.id), True)

        if member_data:
            return LevelingAccount(self.database, self.table, member.guild.id, member.id, self.rank_multiplier)

        return None

    def get_leaderboard(self, guild):
        guild_info = self.database.select([], self.table, [{'guild': guild.id}], True)
        members = [LevelingAccount(self.database, self.table, *member_info[:2], self.rank_multiplier)
                   for member_info in guild_info]

        members.sort()
        return members
