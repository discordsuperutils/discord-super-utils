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
        amt = 0
        for code in self.invite_list:
            amt += int(code.uses)
        return amt


class InviteTracker:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache = {}
        self.bot.add_listener(self.setcache, 'on_ready')
        self.bot.add_listener(self.remove_guildcache, 'on_guild_remove')
        self.bot.add_listener(self.updateguildcache, 'on_guild_add')
        self.bot.add_listener(self.updatecache, 'on_invite_create')
        self.bot.add_listener(self.removecache, 'on_invite_delete')

    @classmethod
    async def get_code(cls, invite: discord.Invite):
        for inv in await invite.guild.invites():
            if inv.code == invite.code:
                return invite

    @classmethod
    async def check_invites(cls, invite: discord.Invite):
        invite = await cls.get_code(invite)
        for inv in await invite.guild.invites():
            if invite.uses > inv.uses and inv.code == invite.code:
                return invite

    async def getinvite(self, member: discord.Member):
        for invite in self.cache[member.guild.id].values():
            for inv in await member.guild.invites():
                if not invite.revoked:
                    if invite.code == inv.code and inv.uses - invite.uses == 1:
                        self.cache[member.guild.id][invite.code].uses += 1
                        return inv
                    else:
                        return None
                else:
                    self.cache[member.guild.id].pop(invite.code)
                    return None

    async def get_user_invites(self, member: discord.Member):
        """Returns a list of invite objects that the user created"""
        invites = []
        for invite in self.cache[member.guild.id].values():
            if invite.inviter.id == member.id:
                invites.append(invite)
        return invites

    # Cache updates ---------------------------------------------

    async def setcache(self):
        data = {}
        for guild in self.bot.guilds:
            for invite in await guild.invites():
                data[invite.code] = invite
            self.cache[guild.id] = data

    async def updateguildcache(self, guild: discord.Guild):
        data = {}
        for invite in await guild.invites():
            data[invite.code] = invite
        self.cache[guild.id] = data

    async def updatecache(self, invite: discord.Invite):
        self.cache[invite.guild.id][invite.code] = invite

    async def removecache(self, invite: discord.Invite):
        self.cache[invite.guild.id].pop(invite.code)

    async def remove_guildcache(self, guild: discord.Guild):
        self.cache.pop(guild.id)

    # cache updates ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    async def fetch_inviter(self, member: discord.Member):
        """Can be called in on_member_join. Fetches the member object of the user that created the invite"""
        invite = await self.getinvite(member)
        return member.guild.get_member(invite.inviter.id)

    async def fetch_user_info(self, member: discord.Member):
        """Returns InviteUser Object"""
        return InviteUser(member, await self.get_user_invites(member))

# Started work on InviteTracker Class. I am tired, I'll finish tomorrow cause, I don't wanna mess up my sleep schedule.
