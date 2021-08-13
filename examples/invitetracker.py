import discord
from discordSuperUtils import InviteTracker
from discord.ext import commands

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
inv = InviteTracker(bot)


@bot.event
async def on_ready():
    print(f"ready")


@bot.event
async def on_member_join(member):
    inviter = await inv.fetch_inviter(member)
    channel = bot.get_channel(844031582305648701)
    await channel.send(f"{member.mention} was invited by {inviter.mention}")


@bot.command()
async def info(ctx, member: discord.Member = None):
    member = ctx.author if not member else member
    data = await inv.fetch_user_info(member)
    await ctx.send(data)

bot.run("token")
