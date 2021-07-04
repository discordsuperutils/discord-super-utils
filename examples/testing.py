import discord
from discord.ext import commands
from discordSuperUtils.Imaging import ImageManager

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)

imgmanager = ImageManager(bot)

@bot.event
async def on_ready():
    print(bot.user)
    imgmanager.create_card()

@bot.command()
async def gay(ctx, member : discord.Member = None):
    member = ctx.author if not member else member
    img = imgmanager.add_gay(member.avatar_url)
    await ctx.send(file=img)

@bot.command()
async def sex(ctx, member1 :discord.Member, member2 : discord.Member):
    img = imgmanager.merge_image(member1.avatar_url, member2.avatar_url)
    await ctx.send(file=img)

@bot.command()
async def test(ctx, member: discord.Member = None):
    member = ctx.author if not member else member
    img = imgmanager.create_profile(member, 2, 100, 1000)
    await ctx.send(file=img)

bot.run("ODEwNjE2NDc3ODM3Mjk1NjYw.YCmPbA.f1q1TAuCdTbeacGyJLxE_diellw")

