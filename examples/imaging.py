import discord
from discord.ext import commands

import discordSuperUtils

bot = commands.Bot(command_prefix="-", intents=discord.Intents.all())
ImageManager = discordSuperUtils.ImageManager()


@bot.event
async def on_ready():
    print('Image manager is ready.', bot.user)


@bot.command()
async def test_welcome(ctx):
    member = ctx.author

    await ctx.send(file=await ImageManager.create_welcome_card(
        member,
        discordSuperUtils.Backgrounds.GAMING,
        (255, 255, 255),
        f"Welcome, {member} 🔥",
        "Welcome to ?,! Please read the #rules.",
        transparency=127
    ))


bot.run("token")
