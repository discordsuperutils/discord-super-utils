from .Database import DatabaseManager
import time
import math
from .Base import EventManager


database_keys = ['guild', 'member', 'rank', 'xp', 'level_up']


class LevelingManager(EventManager):
    def __init__(self, database: DatabaseManager, table, bot, xp_on_message=5, rank_multiplier=1.5):
        super().__init__()
        self.database = database
        self.table = table
        self.bot = bot
        self.xp_on_message = xp_on_message
        self.rank_multiplier = rank_multiplier

        self.cooldown_members = {}
        self.bot.add_listener(self.__handle_experience, "on_message")
        self.database.createtable(self.table, [{'name': key, 'type': 'INTEGER'} for key in database_keys], True)

    async def __handle_experience(self, message):
        if not message.guild or message.author.bot:
            return

        if message.guild.id not in self.cooldown_members:
            self.cooldown_members[message.guild.id] = {}

        self.create_account(message.author)
        member_timestamp = self.cooldown_members[message.guild.id].get(message.author.id, 0)

        if (time.time() - member_timestamp) >= 10:
            await self.add_experience(message, self.xp_on_message, self.rank_multiplier)
            self.cooldown_members[message.guild.id][message.author.id] = time.time()

    def create_account(self, member):
        self.database.insertifnotexists(database_keys, [member.guild.id, member.id, 1, 0, 50],
                                        self.table, [{'guild': member.guild.id}, {'member': member.id}])

    async def add_experience(self, message, xp, rank_multiplier):
        member_data = self.get_account(message.author)
        if not member_data:
            return

        member_data['xp'] += xp

        leveled_up = False
        while member_data['xp'] >= member_data['level_up']:
            member_data['level_up'] *= rank_multiplier
            member_data['rank'] += 1
            leveled_up = True

        self.update_account(member_data)

        if leveled_up:
            await self.call_event('on_level_up', message, member_data)

    def update_account(self, member_data):
        member_data.pop('next_level_percentage', None)

        self.database.update(list(member_data), list(member_data.values()),
                             self.table, [{'guild': member_data["guild"]}, {'member': member_data["member"]}])

    @classmethod
    def format_data(cls, data):
        formatted_member_data = {}
        for key, value in zip(database_keys + ['next_level_percentage'], data):
            formatted_member_data[key] = value

        return formatted_member_data

    def get_account(self, member):
        member_data = self.database.select([], self.table, [{'guild': member.guild.id}, {'member': member.id}])
        if member_data:
            member_data = self.format_data(member_data)

            initial_rank_xp = 0 if member_data['level_up'] == 50 else member_data['level_up'] / self.rank_multiplier
            percentage = math.floor(abs(member_data['xp'] - initial_rank_xp) /
                                    (member_data['level_up'] - initial_rank_xp) * 100)

            member_data['next_level_percentage'] = percentage
            return member_data
        else:
            return None

    def get_leaderboard(self, guild):
        xp_data = self.database.select([], self.table, [{'guild': guild.id}], True)

        guild_xp_data = [self.format_data(member_data) for member_data in xp_data]

        return sorted(guild_xp_data, key=lambda item: item["xp"], reverse=True)