""""
If InviteTracker is used in any way that breaks Discord TOS we, (the DiscordSuperUtils team)
are not responsible or liable in any way.
InviteTracker by DiscordSuperUtils was not intended to violate Discord TOS in any way.
In case we are contacted by Discord, we will remove any and all features that violate the Discord ToS.
Please feel free to read the Discord Terms of Service https://discord.com/terms.
"""

import discord
from discord.ext import commands


class InviteUser:
    def __init__(self, user: discord.Member, invites, ):
        self.user = user
        self.invite_list = invites

    def __str__(self):
        return f"<user={self.user.id} invites={self.invites} users_invited={self.users_invited}>"

    @property
    def invite_codes(self):
        return [invite.code for invite in self.invite_list]

    @property
    def invites(self):
        return len(self.invite_list)

    @property
    def users_invited(self):
        return sum([int(code.uses) for code in self.invite_list])


class InviteTracker:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache = {}

        self.bot.loop.create_task(self.__initialize_cache())

        self.bot.add_listener(self.__cleanup_guild_cache, 'on_guild_remove')
        self.bot.add_listener(self.__update_guild_cache, 'on_guild_add')
        self.bot.add_listener(self.__track_invite, 'on_invite_create')
        self.bot.add_listener(self.__cleanup_invite, 'on_invite_delete')

    async def get_invite(self, member: discord.Member):
        for inv in await member.guild.invites():
            for invite in self.cache[member.guild.id]:
                if not invite.revoked:
                    if invite.code == inv.code and inv.uses - invite.uses == 1:
                        await self.__update_guild_cache(member.guild)
                        return inv

                else:
                    if invite in self.cache[invite.guild.id]:
                        self.cache[invite.guild.id].remove(invite)

    async def get_user_invites(self, member: discord.Member):
        """Returns a list of invite objects that the user created"""
        return [invite for invite in self.cache[member.guild.id] if invite.inviter.id == member.id]

    async def __initialize_cache(self):
        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:
            self.cache[guild.id] = await guild.invites()

    async def __update_guild_cache(self, guild: discord.Guild):
        self.cache[guild.id] = await guild.invites()

    async def __track_invite(self, invite: discord.Invite):
        self.cache[invite.guild.id].append(invite)

    async def __cleanup_invite(self, invite: discord.Invite):
        if invite in self.cache[invite.guild.id]:
            self.cache[invite.guild.id].remove(invite)

    async def __cleanup_guild_cache(self, guild: discord.Guild):
        self.cache.pop(guild.id)

    async def fetch_inviter(self, invite: discord.Invite):
        return await self.bot.fetch_user(invite.inviter.id)

    async def fetch_user_info(self, member: discord.Member):
        """Returns InviteUser Object"""
        return InviteUser(member, await self.get_user_invites(member))
