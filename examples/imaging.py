import discord
from discord.ext import commands

import discordSuperUtils

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)

ImageManager = discordSuperUtils.ImageManager(bot, card_back=3, txt_colour=(255, 64, 99), custom_card_back=False)


@bot.event
async def on_ready():
    print('Imaging manager is ready.', bot.user)


@bot.command()
async def gay(ctx, member: discord.Member = None):
    member = ctx.author if not member else member
    img = await ImageManager.add_gay(member.avatar_url)
    await ctx.send(file=img)


@bot.command()
async def merge(ctx, member1: discord.Member, member2: discord.Member):
    img = await ImageManager.merge_image(member1.avatar_url, member2.avatar_url, if_url=True)
    await ctx.send(file=img)


@bot.command()
async def testrank(ctx, member: discord.Member = None):
    member = ctx.author if not member else member
    img = await ImageManager.create_profile(member, 1, 100, 1230000, 2500000, 100000)
    await ctx.send(file=img)


bot.run("token")
