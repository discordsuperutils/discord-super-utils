import discordSuperUtils
import sqlite3
from discord.ext import commands


database = discordSuperUtils.DatabaseManager.connect(sqlite3.connect("database"))
bot = commands.Bot(command_prefix='-')
EconomyManager = discordSuperUtils.EconomyManager(database, 'economy', bot)


@bot.event
async def on_ready():
    print('Economy manager is ready.', bot.user)


@bot.command()
async def create_account(ctx):
    await EconomyManager.create_account(ctx.author)  # wont create an account if there already is one.
    await ctx.send('Created account.')


@bot.command()
async def beg(ctx):
    account = await EconomyManager.get_account(ctx.author)
    account.change_currency(5)
    await ctx.send("You begged for cash and someone gave you 5 dollars!")


@bot.command()
async def leaderboard(ctx):
    guild_leaderboard = await EconomyManager.get_leaderboard(ctx.guild)
    formatted_leaderboard = [f"Member: {x.member}, Network: {x.net}" for x in guild_leaderboard]

    await discordSuperUtils.PageManager(ctx, discordSuperUtils.generate_embeds(
        formatted_leaderboard,
        title="Economy Leaderboard",
        fields=25,
        description=f"Leaderboard of {ctx.guild}"
    )).run()


bot.run("token")
