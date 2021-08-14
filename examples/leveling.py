import discordSuperUtils
from discord.ext import commands

bot = commands.Bot(command_prefix='-')
LevelingManager = discordSuperUtils.LevelingManager(bot)


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(...)
    await LevelingManager.connect_to_database(database, "xp")

    print('Leveling manager is ready.', bot.user)


@LevelingManager.event()
async def on_level_up(message, member_data):
    await message.reply(f"You are now level {member_data.level}")


@bot.command()
async def rank(ctx):
    member_data = await LevelingManager.get_account(ctx.author)
    await ctx.send(f'You are currently level **{await member_data.level()}**, with **{await member_data.xp()}** XP.')


@bot.command()
async def leaderboard(ctx):
    guild_leaderboard = await LevelingManager.get_leaderboard(ctx.guild)
    formatted_leaderboard = [f"Member: {x.member}, XP: {await x.xp()}" for x in guild_leaderboard]

    await discordSuperUtils.PageManager(ctx, discordSuperUtils.generate_embeds(
        formatted_leaderboard,
        title="Leveling Leaderboard",
        fields=25,
        description=f"Leaderboard of {ctx.guild}"
    )).run()


bot.run("token")
