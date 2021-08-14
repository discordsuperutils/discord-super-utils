import discordSuperUtils
from discord.ext import commands


bot = commands.Bot(command_prefix='-')
EconomyManager = discordSuperUtils.EconomyManager(bot)


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(...)
    await EconomyManager.connect_to_database(database, "economy")

    print('Economy manager is ready.', bot.user)


@bot.command()
async def create_account(ctx):
    await EconomyManager.create_account(ctx.author)  # wont create an account if there already is one.
    await ctx.send('Created account.')


@bot.command()
async def beg(ctx):
    account = await EconomyManager.get_account(ctx.author)
    await account.change_currency(5)
    await ctx.send("You begged for cash and someone gave you 5 dollars!")


@bot.command()
async def leaderboard(ctx):
    guild_leaderboard = await EconomyManager.get_leaderboard(ctx.guild)
    formatted_leaderboard = [f"Member: {x.member}, Network: {await x.net()}" for x in guild_leaderboard]

    await discordSuperUtils.PageManager(ctx, discordSuperUtils.generate_embeds(
        formatted_leaderboard,
        title="Economy Leaderboard",
        fields=25,
        description=f"Leaderboard of {ctx.guild}"
    )).run()


bot.run("token")
