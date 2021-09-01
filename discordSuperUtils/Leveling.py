import math
import time

from .Base import DatabaseChecker


class LevelingAccount:
    def __init__(self, database, table, guild: int, member: int, rank_multiplier=1.5):
        self.database = database
        self.table = table
        self.guild = guild
        self.member = member
        self.rank_multiplier = rank_multiplier

    def __str__(self):
        return f"<Account MEMBER={self.member}, GUILD={self.guild}>"

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

        return min(abs(math.floor(abs(xp - initial_xp) / (level_up - initial_xp) * 100)), 100)

    async def initial_rank_xp(self):
        next_level = await self.next_level()
        return 0 if next_level == 50 else next_level / self.rank_multiplier

    async def set_xp(self, value):
        await self.database.update(self.table, {"xp": value}, self.__checks)

    async def set_level(self, value):
        await self.database.update(self.table, {"rank": value}, self.__checks)

    async def set_next_level(self, value):
        await self.database.update(self.table, {"level_up": value}, self.__checks)


class RoleManager(DatabaseChecker):
    def __init__(self, interval=5):
        super().__init__([{'guild': 'snowflake', 'interval': 'smallnumber', 'roles': 'string'}], ['xp_roles'])
        self.interval = interval

    async def get_roles(self, guild):
        self._check_database()

        role_data = await self.database.select(self.tables["xp_roles"], ['interval', 'roles'], {'guild': guild.id})

        if not role_data:
            return []

        roles = role_data["roles"]
        if isinstance(roles, str):
            role_data["roles"] = [int(role) for role in roles.split('\0') if role]

        return role_data

    async def set_roles(self, guild, data_to_set):
        self._check_database()

        default_values = {'guild': guild.id, 'interval': self.interval, 'roles': ''}

        if 'roles' in data_to_set:
            roles = data_to_set["roles"]
            if not isinstance(roles, (list, tuple)):
                raise TypeError("Roles must be of type list.")

            data_to_set["roles"] = '\0'.join(str(role.id) for role in roles)

        if 'interval' in data_to_set:
            if not isinstance(data_to_set["interval"], int):
                raise TypeError("Interval must be of type int.")

        await self.database.updateorinsert(self.tables["xp_roles"],
                                           data_to_set,
                                           {'guild': guild.id},
                                           dict(data_to_set, **default_values))


class LevelingManager(DatabaseChecker):
    def __init__(self, bot, role_manager=None, xp_on_message=5, rank_multiplier=1.5, xp_cooldown=60):
        super().__init__([
            {'guild': 'snowflake', 'member': 'snowflake', 'rank': 'number', 'xp': 'number', 'level_up': 'number'}
        ], ['xp'])

        self.bot = bot
        self.xp_on_message = xp_on_message
        self.rank_multiplier = rank_multiplier
        self.xp_cooldown = xp_cooldown
        self.role_manager = role_manager

        self.cooldown_members = {}
        self.add_event(self.on_database_connect)

    async def on_database_connect(self):
        self.bot.add_listener(self.__handle_experience, 'on_message')

    @staticmethod
    def generate_checks(guild: int, member: int):
        return {'guild': guild, 'member': member}

    async def __handle_experience(self, message):
        self._check_database()

        if not message.guild or message.author.bot:
            return

        member_cooldown = self.cooldown_members.setdefault(message.guild.id, {}).get(message.author.id, 0)

        if (time.time() - member_cooldown) >= self.xp_cooldown:
            await self.create_account(message.author)
            member_account = await self.get_account(message.author)

            await member_account.set_xp(await member_account.xp() + self.xp_on_message)
            self.cooldown_members[message.guild.id][message.author.id] = time.time()

            leveled_up = False
            while await member_account.xp() >= await member_account.next_level():
                await member_account.set_next_level(await member_account.next_level() * member_account.rank_multiplier)
                await member_account.set_level(await member_account.level() + 1)
                leveled_up = True

            if leveled_up:
                roles = []
                if self.role_manager:
                    role_data = await self.role_manager.get_roles(message.guild)
                    if role_data:
                        member_level = await member_account.level()
                        if member_level % role_data["interval"] == 0 and member_level // role_data["interval"] <= len(role_data["roles"]):
                            roles = [message.guild.get_role(role_id) for role_id in role_data["roles"][:await member_account.level() // role_data["interval"]]]
                            roles.reverse()

                await self.call_event('on_level_up', message, member_account, roles)

                if roles:
                    await message.author.add_roles(*roles)

    async def create_account(self, member):
        self._check_database()

        await self.database.insertifnotexists(self.tables["xp"],
                                              dict(
                                                  zip(
                                                      self.tables_column_data[0],
                                                      [member.guild.id, member.id, 1, 0, 50]
                                                  )
                                              ),
                                              self.generate_checks(member.guild.id, member.id))

    async def get_account(self, member):
        self._check_database()

        member_data = await self.database.select(self.tables["xp"],
                                                 [],
                                                 self.generate_checks(member.guild.id, member.id),
                                                 True)

        if member_data:
            return LevelingAccount(self.database, self.tables['xp'], member.guild.id, member.id, self.rank_multiplier)

        return None

    async def get_leaderboard(self, guild):
        self._check_database()

        guild_info = await self.database.select(self.tables['xp'], [], {'guild': guild.id}, True)

        members = [LevelingAccount(self.database,
                                   self.tables['xp'],
                                   member_info['guild'],
                                   member_info['member'],
                                   rank_multiplier=self.rank_multiplier)
                   for member_info in sorted(guild_info, key=lambda x: x["xp"], reverse=True)]

        return members
