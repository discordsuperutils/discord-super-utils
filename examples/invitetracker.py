import discord
import discordSuperUtils
from discord.ext import commands

bot = commands.Bot(command_prefix="-", intents=discord.Intents.all())
InviteTracker = discordSuperUtils.InviteTracker(bot)


@bot.event
async def on_ready():
    print('Invite tracker is ready.', bot.user)


@bot.event
async def on_member_join(member):
    invite = await InviteTracker.get_invite(member)
    channel = bot.get_channel(...)
    inviter = await InviteTracker.fetch_inviter(invite)
    await channel.send(f"{member.mention} was invited by {inviter.mention if inviter else None} with code {invite.code}")


@bot.command()
async def info(ctx, member: discord.Member = None):
    member = ctx.author if not member else member
    await ctx.send(await InviteTracker.fetch_user_info(member))

bot.run("token")
