import discord
from discord.ext import commands
import discordSuperUtils

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)

ImageManager = discordSuperUtils.ImageManager(bot)


@bot.event
async def on_ready():
    print(bot.user)
    ImageManager.create_card()


@bot.command()
async def gay(ctx, member: discord.Member = None):
    member = ctx.author if not member else member
    img = await ImageManager.add_gay(member.avatar_url)
    await ctx.send(file=img)


@bot.command()
async def sex(ctx, member1: discord.Member, member2: discord.Member):
    img = await ImageManager.merge_image(member1.avatar_url, member2.avatar_url)
    await ctx.send(file=img)


@bot.command()
async def test(ctx, member: discord.Member = None):
    member = ctx.author if not member else member
    img = await ImageManager.create_profile(member, 2, 100, 1000)
    await ctx.send(file=img)


bot.run("token")

