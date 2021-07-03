from .Database import DatabaseManager
import discord

dbkeys = ['guild', 'user', 'currency']

class EconomyManager:
    def __init__(self, database : DatabaseManager, tablename, bot):
        self.database = database
        self.tablename = tablename
        self.bot = bot
        self.database.createtable(self.tablename, [{'name': key, 'type': 'INTEGER'} for key in dbkeys], True)

    async def create_account(self, member : discord.Member):
        self.database.insertifnotexists(dbkeys, [member.guild.id, member.id, 0],
                                        self.tablename, [{'guild': member.guild.id}, {'user': member.id}, {'currency': 0}])

    async def remove_account(self, member: discord.Member):
        self.database.delete(self.tablename, [{'guild' : member.guild.id}, {'user' : member.id}])

    async def add_currency(self, member: discord.Member, currency: int):
        money = self.database.select(['currency'], self.tablename, [{"guild" : member.guild.id}, {'user' : member.id}])
        self.database.update(['currency'], [money + currency], self.tablename, [{'guild' : member.guild.id}, {'member' : member.id}])

    async def remove_currency(self, member: discord.Member, currency: int):
        money = self.database.select(['currency'], self.tablename, [{"guild": member.guild.id}, {'user': member.id}])
        self.database.update(['currency'], [money - currency], self.tablename,[{'guild': member.guild.id}, {'member': member.id}])

    async def get_leaderboard(self, guild):
        money_info = self.database.select([], self.tablename, [{'guild' : guild.id}], True)


