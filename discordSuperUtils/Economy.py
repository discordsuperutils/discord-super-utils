from .Database import DatabaseManager
import discord


database_keys = ['guild', 'member', 'currency', 'bank']


class EconomyAccount:
    def __init__(self, guild: int, member: int, database: DatabaseManager, table):
        self.guild = guild
        self.member = member
        self.database = database
        self.table = table

    def __str__(self):
        return f"<Account MEMBER={self.member}, GUILD={self.guild}>"

    def __repr__(self):
        return f"<Account GUILD={self.guild}, MEMBER={self.member}, CURRENCY={self.currency}, BANK={self.bank}>"

    def __lt__(self, other):
        return self.net < other.net

    @property
    def __checks(self):
        return EconomyManager.generate_checks(self.guild, self.member)

    @property
    def currency(self):
        return self.database.select(['currency'], self.table, self.__checks)[0]

    @property
    def bank(self):
        return self.database.select(['bank'], self.table, self.__checks)[0]

    @property
    def net(self):
        return self.bank + self.currency

    def change_currency(self, amount: int):
        self.database.update(['currency'], [self.currency + amount], self.table, self.__checks)

    def change_bank(self, amount: int):
        self.database.update(['bank'], [self.bank + amount], self.table, self.__checks)


class EconomyManager:
    def __init__(self, database: DatabaseManager, table, bot):
        self.database = database
        self.table = table
        self.bot = bot
        self.database.createtable(self.table, [{'name': key, 'type': 'INTEGER'} for key in database_keys], True)

    @staticmethod
    def generate_checks(guild: int, member: int):
        return [{'guild': guild}, {'member': member}]

    async def create_account(self, member: discord.Member):
        self.database.insertifnotexists(database_keys, [member.guild.id, member.id, 0, 0],
                                        self.table, self.generate_checks(member.guild.id, member.id))

    async def get_account(self, member: discord.Member):
        return EconomyAccount(member.guild.id, member.id, self.database, self.table)

    async def get_leaderboard(self, guild):
        guild_info = self.database.select([], self.table, [{'guild': guild.id}], True)
        members = [EconomyAccount(*member_info[:2], self.database, self.table) for member_info in guild_info]
        members.sort()
        return members
