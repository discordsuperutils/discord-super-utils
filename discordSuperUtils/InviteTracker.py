import discord
from discord.ext import commands


class InviteTracker:
    def __init(self, bot: commands.Bot):
        self.bot = bot
        self.cache = {}
        self.bot.add_listener(self.setcache(self.bot), 'on_ready')
        self.bot.add_listener(self.get_inviter, 'on_guild_join')
        self.bot.add_listener(self.updatecache, 'on_guild_join')
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

    async def setcache(self, bot: commands.Bot):
        data = {}
        for guild in bot.guilds:
            for invite in await guild.invites():
                data[invite.code] = invite
            self.cache[guild.id] = data

    async def updatecache(self, invite: discord.Invite):
        self.cache[invite.guild.id][invite.code] = invite

    async def removecache(self, invite:discord.Invite):
        del self.cache[invite.guild.id][invite.code]

    async def get_inviter(self, invite: discord.Invite):
        invite = self.check_invites(invite)

# Started work on InviteTracker Class. I am tired, I'll finish tomorrow cause, I don't wanna mess up my sleep schedule.
